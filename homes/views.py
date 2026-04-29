import os

import cloudinary.uploader
from django.conf import settings
from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Agent, ChatInquiry, ContactMessage, CounterPayRequest, LiveChatThread, PartialHome, Property
from .models import Agent, ChatInquiry, ContactMessage, CounterPayRequest, LiveChatMessage, LiveChatThread, PartialHome, Property
from .permissions import HasAgentCode, HasOwnerAdminCode
from .serializers import (
    AgentAdminSerializer,
    AgentSerializer,
    ChatInquiryAdminSerializer,
    ChatInquiryCreateSerializer,
    ContactMessageAdminSerializer,
    ContactMessageCreateSerializer,
    CounterPayRequestAdminSerializer,
    CounterPayRequestCreateSerializer,
    PartialHomeAdminSerializer,
    PartialHomeListSerializer,
    PartialHomeUnlockedSerializer,
    LiveChatMessageSerializer,
    LiveChatThreadSerializer,
    PropertyAdminSerializer,
    PropertySerializer,
    UnlockPartialHomeSerializer,
)


APARTMENT_CITY_DEMO = ["Denver", "Austin", "Miami", "Seattle", "Chicago"]


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    lookup_field = "public_id"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AgentAdminSerializer
        return AgentSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    lookup_field = "public_id"

    def _is_admin_request(self):
        return HasOwnerAdminCode().has_permission(self.request, self)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"] or self._is_admin_request():
            return PropertyAdminSerializer
        return PropertySerializer

    def get_queryset(self):
        queryset = Property.objects.select_related("agent").prefetch_related("images", "features")

        search = self.request.query_params.get("search")
        prop_type = self.request.query_params.get("type")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        featured = self.request.query_params.get("featured")
        sort = self.request.query_params.get("sort")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(city__icontains=search)
                | Q(state__icontains=search)
                | Q(address__icontains=search)
            )
        if prop_type and prop_type != "all":
            queryset = queryset.filter(property_type=prop_type)
        if city:
            queryset = queryset.filter(city__iexact=city)
        if state:
            queryset = queryset.filter(state__iexact=state)
        if featured == "1":
            queryset = queryset.filter(is_featured=True)

        if sort == "price-asc":
            queryset = queryset.order_by("price")
        elif sort == "price-desc":
            queryset = queryset.order_by("-price")
        elif sort == "newest":
            queryset = queryset.order_by("-year_built")

        return queryset


class PartialHomeViewSet(viewsets.ModelViewSet):
    lookup_field = "public_id"

    def _is_admin_request(self):
        return HasOwnerAdminCode().has_permission(self.request, self)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "unlock"]:
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"] or self._is_admin_request():
            return PartialHomeAdminSerializer
        return PartialHomeListSerializer

    def get_queryset(self):
        queryset = PartialHome.objects.filter(is_active=True).select_related("agent").prefetch_related("images", "features")
        city = self.request.query_params.get("city")
        prop_type = self.request.query_params.get("type")
        if city:
            queryset = queryset.filter(city__iexact=city)
        if prop_type and prop_type != "all":
            queryset = queryset.filter(property_type=prop_type)
        return queryset

    @action(detail=True, methods=["post"])
    def unlock(self, request, public_id=None):
        home = self.get_object()
        serializer = UnlockPartialHomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["secure_code"] != home.secure_code:
            return Response(
                {"detail": "Incorrect code. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = PartialHomeUnlockedSerializer(home).data
        return Response(data, status=status.HTTP_200_OK)


class CounterPayRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CounterPayRequest.objects.select_related("partial_home")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action == "create":
            return CounterPayRequestCreateSerializer
        return CounterPayRequestAdminSerializer


class ContactMessageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ContactMessage.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action == "create":
            return ContactMessageCreateSerializer
        return ContactMessageAdminSerializer


class ChatInquiryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ChatInquiry.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [HasOwnerAdminCode()]

    def get_serializer_class(self):
        if self.action == "create":
            return ChatInquiryCreateSerializer
        return ChatInquiryAdminSerializer


@api_view(["GET"])
def apartment_city_options(_request):
    return Response({"cities": APARTMENT_CITY_DEMO})


_ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@api_view(["POST"])
def upload_images(request):
    if not HasOwnerAdminCode().has_permission(request, None):
        return Response({"detail": "Forbidden."}, status=403)

    if not (
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    ):
        return Response(
            {"detail": "Cloudinary is not configured. Set Cloudinary keys in backend/.env."},
            status=500,
        )

    files = request.FILES.getlist("images")
    if not files:
        return Response({"detail": "No files provided."}, status=400)

    urls = []
    for file in files:
        _, ext = os.path.splitext(file.name)
        ext = ext.lower()
        if ext not in _ALLOWED_IMAGE_EXTENSIONS:
            return Response(
                {"detail": f"Unsupported file type: {ext or 'unknown'}"},
                status=400,
            )

        uploaded = cloudinary.uploader.upload(
            file,
            folder="fresh-fields-homes",
            resource_type="image",
        )
        urls.append(uploaded.get("secure_url") or uploaded.get("url"))

    return Response({"urls": urls})


# ---------------------------------------------------------------------------
# Agent portal views
# ---------------------------------------------------------------------------


def _get_agent_from_request(request):
    """Return Agent if X-Agent-Code header is valid, else None."""
    code = request.headers.get("X-Agent-Code", "").strip()
    if not code:
        return None
    try:
        return Agent.objects.get(agent_code=code)
    except Agent.DoesNotExist:
        return None


@api_view(["POST"])
def agent_portal_login(request):
    code = (request.data.get("code") or "").strip()
    if not code:
        return Response({"detail": "Code is required."}, status=400)
    try:
        agent = Agent.objects.get(agent_code=code)
    except Agent.DoesNotExist:
        return Response({"detail": "Invalid agent code."}, status=401)
    return Response(AgentSerializer(agent).data, status=200)


@api_view(["GET"])
def agent_portal_properties(request):
    agent = _get_agent_from_request(request)
    if not agent:
        return Response({"detail": "Unauthorized."}, status=401)
    props = (
        Property.objects.filter(agent=agent)
        .prefetch_related("images", "features")
    )
    return Response(PropertySerializer(props, many=True).data)


@api_view(["GET"])
def agent_portal_messages(request):
    agent = _get_agent_from_request(request)
    if not agent:
        return Response({"detail": "Unauthorized."}, status=401)
    contacts = ContactMessage.objects.all().order_by("-created_at")[:50]
    chats = ChatInquiry.objects.all().order_by("-created_at")[:50]
    return Response({
        "contacts": ContactMessageAdminSerializer(contacts, many=True).data,
        "chats": ChatInquiryAdminSerializer(chats, many=True).data,
    })


@api_view(["GET"])
def agent_portal_chat_threads(request):
    if not HasAgentCode().has_permission(request, None):
        return Response({"detail": "Unauthorized."}, status=401)

    agent = _get_agent_from_request(request)
    threads = (
        LiveChatThread.objects.filter(agent=agent)
        .select_related("property")
        .prefetch_related("messages")
    )
    return Response(LiveChatThreadSerializer(threads, many=True).data)


@api_view(["GET"])
def agent_portal_chat_thread_messages(request, thread_id):
    if not HasAgentCode().has_permission(request, None):
        return Response({"detail": "Unauthorized."}, status=401)

    agent = _get_agent_from_request(request)
    thread = LiveChatThread.objects.filter(id=thread_id, agent=agent).first()
    if not thread:
        return Response({"detail": "Thread not found."}, status=404)

    messages = thread.messages.all()
    return Response(LiveChatMessageSerializer(messages, many=True).data)


def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


@api_view(["POST"])
def user_chat_start(request):
    property_id = (request.data.get("property_id") or "").strip()
    if not property_id:
        return Response({"detail": "property_id required."}, status=400)

    prop = Property.objects.select_related("agent").filter(public_id=property_id).first()
    if not prop:
        return Response({"detail": "Property not found."}, status=404)

    user_ip = _get_client_ip(request)
    thread, _ = LiveChatThread.objects.get_or_create(
        property=prop,
        user_ip=user_ip,
        defaults={"agent": prop.agent},
    )

    return Response({
        "thread_id": thread.id,
        "agent": {
            "id": prop.agent.public_id,
            "name": prop.agent.name,
            "phone": getattr(prop.agent, "phone", ""),
            "email": prop.agent.email,
            "image": prop.agent.image,
        },
    })


@api_view(["POST"])
def user_chat_send(request, thread_id):
    user_ip = _get_client_ip(request)
    thread = LiveChatThread.objects.filter(id=thread_id, user_ip=user_ip).first()
    if not thread:
        return Response({"detail": "Thread not found."}, status=404)

    text = (request.data.get("text") or "").strip()
    if not text:
        return Response({"detail": "text required."}, status=400)

    message = LiveChatMessage.objects.create(
        thread=thread,
        sender=LiveChatMessage.SENDER_USER,
        text=text,
    )
    return Response(LiveChatMessageSerializer(message).data, status=201)


@api_view(["GET"])
def user_chat_messages(request, thread_id):
    user_ip = _get_client_ip(request)
    thread = LiveChatThread.objects.filter(id=thread_id, user_ip=user_ip).first()
    if not thread:
        return Response({"detail": "Thread not found."}, status=404)

    messages_qs = thread.messages.all()
    since_id = request.query_params.get("since")
    if since_id:
        try:
            messages_qs = messages_qs.filter(id__gt=int(since_id))
        except ValueError:
            pass

    return Response(LiveChatMessageSerializer(messages_qs, many=True).data)


@api_view(["POST"])
def agent_portal_chat_thread_reply(request, thread_id):
    if not HasAgentCode().has_permission(request, None):
        return Response({"detail": "Unauthorized."}, status=401)

    agent = _get_agent_from_request(request)
    thread = LiveChatThread.objects.filter(id=thread_id, agent=agent).first()
    if not thread:
        return Response({"detail": "Thread not found."}, status=404)

    text = (request.data.get("text") or "").strip()
    if not text:
        return Response({"detail": "text required."}, status=400)

    message = LiveChatMessage.objects.create(
        thread=thread,
        sender=LiveChatMessage.SENDER_AGENT,
        text=text,
    )
    return Response(LiveChatMessageSerializer(message).data, status=201)
