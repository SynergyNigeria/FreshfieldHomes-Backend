from django.urls import re_path

from .consumers import AgentChatConsumer, PropertyChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<property_id>[\w-]+)/$", PropertyChatConsumer.as_asgi()),
    re_path(r"^ws/agent-chat/$", AgentChatConsumer.as_asgi()),
]
