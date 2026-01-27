from rest_framework import permissions


class IsCoach(permissions.BasePermission):
    """Permission class to check if user is a coach."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'coach'
        )


class IsClient(permissions.BasePermission):
    """Permission class to check if user is a client."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'client'
        )


class IsCoachOrAssistant(permissions.BasePermission):
    """Permission class to check if user is a coach or assistant."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['coach', 'assistant']
        )
