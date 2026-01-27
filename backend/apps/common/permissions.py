"""
Reusable DRF permission classes for role-based access control.
"""
from rest_framework import permissions


class IsCoach(permissions.BasePermission):
    """
    Permission class to check if user is a coach.
    Only coaches can access coach portal endpoints.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'coach'
        )


class IsClient(permissions.BasePermission):
    """
    Permission class to check if user is a client.
    Only clients can access client portal endpoints.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )


class IsCoachOrAssistant(permissions.BasePermission):
    """
    Permission class to check if user is a coach or assistant.
    Both coaches and assistants can access coach portal endpoints.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['coach', 'assistant']
        )


def get_client_from_user(user):
    """
    Helper function to safely get Client from User.
    Returns Client instance or None if not linked.
    Raises Client.DoesNotExist if user has no linked client.
    """
    from apps.clients.models import Client
    
    if not user or not user.is_authenticated:
        return None
    
    if user.role != 'client':
        return None
    
    try:
        return Client.objects.get(user=user)
    except Client.DoesNotExist:
        return None
