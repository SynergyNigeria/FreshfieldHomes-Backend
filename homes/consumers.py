import json
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Agent, LiveChatMessage, LiveChatThread, Property
from .serializers import LiveChatMessageSerializer, LiveChatThreadSerializer


def _client_ip_from_scope(scope) -> str:
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    client = scope.get("client")
    if client and len(client) > 0:
        return str(client[0])

    return "0.0.0.0"


class PropertyChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        property_id = self.scope["url_route"]["kwargs"].get("property_id")
        if not property_id:
            await self.close(code=4001)
            return

        self.property = await sync_to_async(Property.objects.select_related("agent").filter(public_id=property_id).first)()
        if not self.property:
            await self.close(code=4004)
            return

        user_ip = _client_ip_from_scope(self.scope)
        self.thread = await self._get_or_create_thread(self.property, user_ip)
        self.thread_group = f"live_chat_thread_{self.thread.id}"
        self.agent_group = f"live_chat_agent_{self.property.agent.public_id}"

        await self.channel_layer.group_add(self.thread_group, self.channel_name)
        await self.channel_layer.group_add(self.agent_group, self.channel_name)
        await self.accept()

        messages = await self._serialized_thread_messages(self.thread)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "init",
                    "threadId": self.thread.id,
                    "propertyId": self.property.public_id,
                    "agent": {
                        "id": self.property.agent.public_id,
                        "name": self.property.agent.name,
                        "phone": self.property.agent.phone,
                        "email": self.property.agent.email,
                        "image": self.property.agent.image,
                    },
                    "messages": messages,
                }
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "thread_group"):
            await self.channel_layer.group_discard(self.thread_group, self.channel_name)
        if hasattr(self, "agent_group"):
            await self.channel_layer.group_discard(self.agent_group, self.channel_name)

    async def receive(self, text_data):
        payload = json.loads(text_data or "{}")
        if payload.get("type") != "chat_message":
            return

        text = (payload.get("text") or "").strip()
        if not text:
            return

        message = await self._create_message(self.thread, LiveChatMessage.SENDER_USER, text)
        serialized = await self._serialize_message(message)
        thread = await self._serialize_thread(self.thread)

        await self.channel_layer.group_send(
            self.thread_group,
            {"type": "broadcast_message", "threadId": self.thread.id, "message": serialized},
        )
        await self.channel_layer.group_send(
            self.agent_group,
            {"type": "broadcast_thread_update", "thread": thread},
        )

    async def broadcast_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "threadId": event["threadId"],
                    "message": event["message"],
                }
            )
        )

    async def broadcast_thread_update(self, event):
        await self.send(text_data=json.dumps({"type": "thread_updated", "thread": event["thread"]}))

    @staticmethod
    @sync_to_async
    def _get_or_create_thread(property_obj, user_ip):
        thread, _ = LiveChatThread.objects.get_or_create(
            property=property_obj,
            user_ip=user_ip,
            defaults={"agent": property_obj.agent},
        )
        return thread

    @staticmethod
    @sync_to_async
    def _create_message(thread, sender, text):
        message = LiveChatMessage.objects.create(thread=thread, sender=sender, text=text)
        LiveChatThread.objects.filter(id=thread.id).update(updated_at=message.created_at)
        thread.refresh_from_db()
        return message

    @staticmethod
    @sync_to_async
    def _serialize_message(message):
        return LiveChatMessageSerializer(message).data

    @staticmethod
    @sync_to_async
    def _serialize_thread(thread):
        thread.refresh_from_db()
        return LiveChatThreadSerializer(thread).data

    @staticmethod
    @sync_to_async
    def _serialized_thread_messages(thread):
        messages = thread.messages.all()
        return LiveChatMessageSerializer(messages, many=True).data


class AgentChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query = parse_qs(self.scope.get("query_string", b"").decode())
        code = (query.get("agent_code", [""])[0] or "").strip()
        if not code:
            await self.close(code=4401)
            return

        self.agent = await sync_to_async(Agent.objects.filter(agent_code=code).first)()
        if not self.agent:
            await self.close(code=4401)
            return

        self.agent_group = f"live_chat_agent_{self.agent.public_id}"
        await self.channel_layer.group_add(self.agent_group, self.channel_name)
        await self.accept()

        threads = await self._serialize_agent_threads(self.agent)
        await self.send(text_data=json.dumps({"type": "threads", "threads": threads}))

    async def disconnect(self, close_code):
        if hasattr(self, "agent_group"):
            await self.channel_layer.group_discard(self.agent_group, self.channel_name)

    async def receive(self, text_data):
        payload = json.loads(text_data or "{}")
        if payload.get("type") != "agent_message":
            return

        thread_id = payload.get("threadId")
        text = (payload.get("text") or "").strip()
        if not thread_id or not text:
            return

        thread = await sync_to_async(
            LiveChatThread.objects.select_related("agent").filter(id=thread_id, agent=self.agent).first
        )()
        if not thread:
            return

        message = await self._create_message(thread, LiveChatMessage.SENDER_AGENT, text)
        serialized_message = await self._serialize_message(message)
        serialized_thread = await self._serialize_thread(thread)
        thread_group = f"live_chat_thread_{thread.id}"

        await self.channel_layer.group_send(
            thread_group,
            {"type": "broadcast_message", "threadId": thread.id, "message": serialized_message},
        )
        await self.channel_layer.group_send(
            self.agent_group,
            {"type": "broadcast_thread_update", "thread": serialized_thread},
        )

    async def broadcast_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "threadId": event["threadId"],
                    "message": event["message"],
                }
            )
        )

    async def broadcast_thread_update(self, event):
        await self.send(text_data=json.dumps({"type": "thread_updated", "thread": event["thread"]}))

    @staticmethod
    @sync_to_async
    def _create_message(thread, sender, text):
        message = LiveChatMessage.objects.create(thread=thread, sender=sender, text=text)
        LiveChatThread.objects.filter(id=thread.id).update(updated_at=message.created_at)
        thread.refresh_from_db()
        return message

    @staticmethod
    @sync_to_async
    def _serialize_message(message):
        return LiveChatMessageSerializer(message).data

    @staticmethod
    @sync_to_async
    def _serialize_thread(thread):
        thread.refresh_from_db()
        return LiveChatThreadSerializer(thread).data

    @staticmethod
    @sync_to_async
    def _serialize_agent_threads(agent):
        threads = LiveChatThread.objects.filter(agent=agent).select_related("property").prefetch_related("messages")
        return LiveChatThreadSerializer(threads, many=True).data
