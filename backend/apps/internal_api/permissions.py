"""
Internal API: require X-Internal-Token header matching INTERNAL_API_TOKEN.
Used only for /api/internal/* endpoints (MCP, cron, server-to-server).
"""
from rest_framework import permissions
from django.conf import settings


class InternalTokenPermission(permissions.BasePermission):
    """
    Allow only requests that include header X-Internal-Token with the value
    of settings.INTERNAL_API_TOKEN. No JWT/session required.
    """
    message = 'Missing or invalid X-Internal-Token header.'

    def has_permission(self, request, view):
        token = request.headers.get('X-Internal-Token') or request.META.get('HTTP_X_INTERNAL_TOKEN')
        expected = getattr(settings, 'INTERNAL_API_TOKEN', None)
        if not expected:
            return False
        return token == expected
