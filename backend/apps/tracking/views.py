from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.common.permissions import IsCoachOrAssistant
from .models import CheckIn
from .serializers import CheckInSerializer, CheckInCreateSerializer


class CheckInViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing client check-ins (coach only).
    """
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filterset_fields = ['client', 'date']
    search_fields = ['notes']
    
    def get_queryset(self):
        """Filter check-ins by client if client_id is provided in URL."""
        queryset = CheckIn.objects.all()
        client_id = self.kwargs.get('client_pk')
        if client_id is not None:
            queryset = queryset.filter(client_id=client_id)
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return CheckInCreateSerializer
        return CheckInSerializer
    
    def perform_create(self, serializer):
        """Set the client when creating a check-in."""
        client_id = self.kwargs.get('client_pk')
        if client_id:
            from apps.clients.models import Client
            client = Client.objects.get(id=client_id)
            serializer.save(client=client)
        else:
            serializer.save()


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for generating reports (coach only).
    """
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    
    def get_queryset(self):
        # This will be implemented later with actual report logic
        return CheckIn.objects.none()
