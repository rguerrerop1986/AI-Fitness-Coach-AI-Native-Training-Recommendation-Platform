"""
Utilities for resolving the authenticated client from a request.
Raises clear errors when user is not authenticated or has no/incomplete client profile.
"""
from rest_framework.request import Request

from apps.clients.models import Client


class ClientResolutionError(Exception):
    """Raised when the client cannot be resolved from the request."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_authenticated_client(request: Request) -> Client:
    """
    Get the Client instance for the authenticated user.
    Reusable for dashboard and any client-scoped endpoint.

    Raises:
        ClientResolutionError: If no user, not a client role, no ClientProfile, or profile incomplete.
    """
    if not request or not request.user:
        raise ClientResolutionError(
            'Authentication required.',
            status_code=401,
        )
    if not request.user.is_authenticated:
        raise ClientResolutionError(
            'Authentication required.',
            status_code=401,
        )
    if getattr(request.user, 'role', None) != 'client':
        raise ClientResolutionError(
            'This endpoint is for client users only.',
            status_code=403,
        )
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        raise ClientResolutionError(
            'Client profile not found. Please contact your coach.',
            status_code=404,
        )
    # Basic completeness: must have names and at least one of height/weight for recommendations
    if not (client.first_name and client.last_name):
        raise ClientResolutionError(
            'Client profile is incomplete (missing name). Please contact your coach.',
            status_code=400,
        )
    return client
