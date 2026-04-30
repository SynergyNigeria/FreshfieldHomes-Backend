from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentViewSet,
    ChatInquiryViewSet,
    cloudinary_connectivity,
    cloudinary_upload_signature,
    ContactMessageViewSet,
    CounterPayRequestViewSet,
    PartialHomeViewSet,
    PropertyViewSet,
    agent_portal_chat_thread_messages,
    agent_portal_chat_thread_reply,
    agent_portal_chat_threads,
    agent_portal_login,
    agent_portal_messages,
    agent_portal_properties,
    apartment_city_options,
    upload_images,
    user_chat_messages,
    user_chat_send,
    user_chat_start,
)

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"partial-homes", PartialHomeViewSet, basename="partial-home")
router.register(r"counter-pay-requests", CounterPayRequestViewSet, basename="counter-pay-request")
router.register(r"contact-messages", ContactMessageViewSet, basename="contact-message")
router.register(r"chat-inquiries", ChatInquiryViewSet, basename="chat-inquiry")

urlpatterns = [
    path("", include(router.urls)),
    path("meta/apartment-cities/", apartment_city_options, name="apartment-city-options"),
    path("meta/cloudinary-connectivity/", cloudinary_connectivity, name="cloudinary-connectivity"),
    path("cloudinary-upload-signature/", cloudinary_upload_signature, name="cloudinary-upload-signature"),
    path("upload-images/", upload_images, name="upload-images"),
    path("agent-portal/login/", agent_portal_login, name="agent-portal-login"),
    path("agent-portal/properties/", agent_portal_properties, name="agent-portal-properties"),
    path("agent-portal/messages/", agent_portal_messages, name="agent-portal-messages"),
    path("agent-portal/chat-threads/", agent_portal_chat_threads, name="agent-portal-chat-threads"),
    path("agent-portal/chat-threads/<int:thread_id>/messages/", agent_portal_chat_thread_messages, name="agent-portal-chat-thread-messages"),
    path("agent-portal/chat-threads/<int:thread_id>/reply/", agent_portal_chat_thread_reply, name="agent-portal-chat-thread-reply"),
    path("chat/start/", user_chat_start, name="user-chat-start"),
    path("chat/<int:thread_id>/send/", user_chat_send, name="user-chat-send"),
    path("chat/<int:thread_id>/messages/", user_chat_messages, name="user-chat-messages"),
]
