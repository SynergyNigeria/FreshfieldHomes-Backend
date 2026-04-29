from django.conf import settings
from rest_framework.permissions import BasePermission

from .models import Agent


class HasOwnerAdminCode(BasePermission):
    message = "Invalid owner admin code."

    def has_permission(self, request, view):
        return request.headers.get("X-Admin-Code", "") == settings.OWNER_ADMIN_CODE


class HasAgentCode(BasePermission):
    message = "Invalid agent code."

    def has_permission(self, request, view):
        agent_code = request.headers.get("X-Agent-Code", "").strip()
        if not agent_code:
            return False
        return Agent.objects.filter(agent_code=agent_code).exists()
