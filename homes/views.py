import os
import socket
import time

import cloudinary.uploader
import cloudinary.utils
from django.conf import settings
from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Agent, AgentApplication, ChatInquiry, ContactMessage, CounterPayRequest, LiveChatMessage, LiveChatThread, PartialHome, Property
from .permissions import HasAgentCode, HasOwnerAdminCode
from .serializers import (
    AgentAdminSerializer,
    AgentApplicationCreateSerializer,
    AgentApplicationSerializer,
    AgentApplicationStatusSerializer,
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


@api_view(["GET"])
def cloudinary_connectivity(_request):
    host = "api.cloudinary.com"
    port = 443
    try:
        with socket.create_connection((host, port), timeout=5):
            pass
    except OSError as exc:
        return Response(
            {
                "reachable": False,
                "host": host,
                "port": port,
                "detail": "Backend cannot reach Cloudinary over HTTPS.",
                "error": str(exc),
            },
            status=503,
        )

    return Response(
        {
            "reachable": True,
            "host": host,
            "port": port,
            "detail": "Backend can reach Cloudinary over HTTPS.",
        }
    )


@api_view(["POST"])
def cloudinary_upload_signature(request):
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

    folder = "fresh-fields-homes"
    timestamp = int(time.time())
    params_to_sign = {
        "folder": folder,
        "timestamp": timestamp,
    }
    signature = cloudinary.utils.api_sign_request(
        params_to_sign,
        settings.CLOUDINARY_API_SECRET,
    )

    return Response(
        {
            "cloudName": settings.CLOUDINARY_CLOUD_NAME,
            "apiKey": settings.CLOUDINARY_API_KEY,
            "folder": folder,
            "timestamp": timestamp,
            "signature": signature,
        }
    )


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

        try:
            uploaded = cloudinary.uploader.upload(
                file,
                folder="fresh-fields-homes",
                resource_type="image",
            )
        except Exception as exc:
            return Response(
                {
                    "detail": "Image upload service is temporarily unreachable from backend.",
                    "hint": "Use /api/cloudinary-upload-signature/ and upload from browser directly.",
                    "error": str(exc),
                },
                status=503,
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


# ---------------------------------------------------------------------------
# Agent application views
# ---------------------------------------------------------------------------

@api_view(["POST"])
def agent_application_create(request):
    """Public endpoint: anyone can submit an agent application."""
    serializer = AgentApplicationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    application = serializer.save()
    return Response(AgentApplicationSerializer(application).data, status=201)


@api_view(["GET"])
def agent_application_list(request):
    """Admin: list all applications."""
    if not HasOwnerAdminCode().has_permission(request, None):
        return Response({"detail": "Forbidden."}, status=403)
    apps = AgentApplication.objects.all()
    return Response(AgentApplicationSerializer(apps, many=True).data)


@api_view(["POST"])
def agent_application_decide(request, app_id):
    """Admin: approve or reject an application."""
    if not HasOwnerAdminCode().has_permission(request, None):
        return Response({"detail": "Forbidden."}, status=403)

    try:
        application = AgentApplication.objects.get(pk=app_id)
    except AgentApplication.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    serializer = AgentApplicationStatusSerializer(application, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    decision = request.data.get("status")
    if decision not in ("approved", "rejected"):
        return Response({"detail": "status must be 'approved' or 'rejected'."}, status=400)

    if decision == "approved" and not application.payment_token:
        import secrets
        application.payment_token = secrets.token_urlsafe(32)

    serializer.save()
    return Response(AgentApplicationSerializer(application).data)


@api_view(["GET"])
def agent_application_status(request):
    """Public: check application status by email."""
    email = (request.query_params.get("email") or "").strip().lower()
    if not email:
        return Response({"detail": "email query param required."}, status=400)
    try:
        application = AgentApplication.objects.get(email__iexact=email)
    except AgentApplication.DoesNotExist:
        return Response({"detail": "No application found for this email."}, status=404)
    return Response(AgentApplicationSerializer(application).data)


@api_view(["POST"])
def agent_application_initialize_payment(request):
    """
    Validates the applicant and returns the NGN kobo amount for $25.
    The frontend uses this amount to open the Paystack inline popup directly
    (no server-side Paystack API call needed — avoids IP/firewall issues).
    """
    import urllib.request
    import json as _json

    email = (request.data.get("email") or "").strip().lower()
    token = (request.data.get("payment_token") or "").strip()

    if not email or not token:
        return Response({"detail": "email and payment_token are required."}, status=400)

    try:
        application = AgentApplication.objects.get(email__iexact=email)
    except AgentApplication.DoesNotExist:
        return Response({"detail": "Application not found."}, status=404)

    if application.status != "approved":
        return Response({"detail": "Application is not in an approved state."}, status=400)

    if application.payment_token != token:
        return Response({"detail": "Invalid payment token."}, status=400)

    # Fetch live USD→NGN rate
    try:
        with urllib.request.urlopen(
            "https://open.er-api.com/v6/latest/USD", timeout=5
        ) as resp:
            rate_data = _json.loads(resp.read())
        ngn_rate = float(rate_data["rates"]["NGN"])
    except Exception:
        ngn_rate = 1600.0  # Fallback if exchange API is unavailable

    amount_kobo = int(round(25 * ngn_rate * 100))

    return Response({
        "amount_kobo": amount_kobo,
        "ngn_rate": ngn_rate,
    })


@api_view(["POST"])
def agent_application_complete_payment(request):
    """
    Called after Paystack inline payment succeeds on the frontend.
    Security is enforced by the payment_token (a secret set server-side on approval).
    The Paystack reference is stored for manual reconciliation in the Paystack dashboard.
    """
    email = (request.data.get("email") or "").strip().lower()
    token = (request.data.get("payment_token") or "").strip()
    paystack_reference = (request.data.get("paystack_reference") or "").strip()

    if not email or not token:
        return Response({"detail": "email and payment_token are required."}, status=400)

    if not paystack_reference:
        return Response({"detail": "paystack_reference is required."}, status=400)

    try:
        application = AgentApplication.objects.get(email__iexact=email)
    except AgentApplication.DoesNotExist:
        return Response({"detail": "Application not found."}, status=404)

    if application.status == "paid":
        return Response({"detail": "Already activated."}, status=400)

    if application.status != "approved":
        return Response({"detail": "Application is not approved."}, status=400)

    if application.payment_token != token:
        return Response({"detail": "Invalid payment token."}, status=400)

    # Create the Agent record if not already there
    agent, created = Agent.objects.get_or_create(
        email__iexact=application.email,
        defaults={
            "name": application.full_name,
            "phone": application.phone,
            "email": application.email,
            "image": "",
        },
    )
    if not created:
        agent.name = application.full_name
        agent.phone = application.phone
        agent.save(update_fields=["name", "phone"])

    application.status = "paid"
    application.paystack_reference = paystack_reference
    application.save(update_fields=["status", "paystack_reference", "updated_at"])

    return Response({
        "detail": "Payment confirmed. Your agent account is now active.",
        "agent_code": agent.agent_code,
    })
