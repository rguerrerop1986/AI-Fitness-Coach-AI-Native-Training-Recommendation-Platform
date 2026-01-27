from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from apps.common.permissions import IsCoachOrAssistant
from .models import Client, Measurement
from .serializers import (
    ClientSerializer, ClientCreateSerializer, 
    MeasurementSerializer, ClientMeasurementSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for client management (coach only)."""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'sex']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a client (soft delete)."""
        client = self.get_object()
        client.is_active = False
        client.save()
        return Response({'message': 'Client archived successfully.'})
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived client."""
        client = self.get_object()
        client.is_active = True
        client.save()
        return Response({'message': 'Client restored successfully.'})


class MeasurementViewSet(viewsets.ModelViewSet):
    """ViewSet for client measurements (coach only)."""
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date']
    ordering_fields = ['date', 'weight_kg']
    ordering = ['-date']
    
    def get_queryset(self):
        client_id = self.kwargs.get('client_pk')
        return Measurement.objects.filter(client_id=client_id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientMeasurementSerializer
        return MeasurementSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['client_id'] = self.kwargs.get('client_pk')
        return context
