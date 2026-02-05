from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from apps.common.permissions import IsCoachOrAssistant
from .models import Client, Measurement
from django.contrib.auth import get_user_model
from .serializers import (
    ClientSerializer, ClientCreateSerializer,
    DeactivateClientSerializer,
    MeasurementSerializer, ClientMeasurementSerializer,
    ClientSetPasswordSerializer
)

User = get_user_model()


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        # Return full client with portal_username so coach knows login credentials
        return Response(
            ClientSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        # List: default only active. Detail actions (retrieve, update, deactivate, reactivate) see all.
        if self.action == 'list' and 'is_active' not in self.request.query_params:
            queryset = queryset.filter(is_active=True)
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Deactivate client (soft delete), cancel all future appointments in one transaction."""
        client = self.get_object()
        serializer = DeactivateClientSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        reason = (serializer.validated_data.get('reason') or '').strip() or 'Cliente dado de baja'

        from apps.appointments.models import Appointment

        with transaction.atomic():
            future = Appointment.objects.filter(
                client=client,
                scheduled_at__gt=timezone.now(),
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.NO_SHOW],
            )
            cancelled_count = future.update(status=Appointment.Status.CANCELLED)
            client.is_active = False
            client.deactivated_at = timezone.now()
            client.deactivated_by = request.user
            client.deactivation_reason = reason
            client.save(update_fields=['is_active', 'deactivated_at', 'deactivated_by', 'deactivation_reason', 'updated_at'])

        data = ClientSerializer(client).data
        data['cancelled_appointments_count'] = cancelled_count
        return Response(data)

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        """Reactivate client. Does not restore previously cancelled appointments."""
        client = self.get_object()
        client.is_active = True
        client.deactivated_at = None
        client.deactivated_by = None
        client.deactivation_reason = ''
        client.save(update_fields=['is_active', 'deactivated_at', 'deactivated_by', 'deactivation_reason', 'updated_at'])
        return Response(ClientSerializer(client).data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a client (soft delete). Alias for deactivate without cancelling appointments."""
        return self.deactivate(request, pk)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived client. Alias for reactivate."""
        return self.reactivate(request, pk)

    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """Set or update portal password for a client. Creates User if it doesn't exist."""
        client = self.get_object()
        serializer = ClientSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']

        if client.user_id:
            # Update existing user password
            user = client.user
            user.set_password(password)
            user.save()
            message = 'Password updated successfully.'
        else:
            # Create new user for client
            email = client.email
            username = email[:150] if len(email) > 150 else email
            if User.objects.filter(username__iexact=username).exists():
                username = f"client_{client.id}"

            # Check if email is already used by another user
            if User.objects.filter(email__iexact=email).exists():
                return Response(
                    {'error': f'A user with email {email} already exists. Cannot create portal access.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User(
                username=username,
                email=email,
                first_name=client.first_name,
                last_name=client.last_name,
                role=User.Role.CLIENT,
            )
            user.set_password(password)
            user.save()
            client.user = user
            client.save(update_fields=['user'])
            message = 'Portal access created successfully. Client can now log in.'

        return Response({
            'message': message,
            'portal_username': user.username,
            'has_portal_access': True,
        })


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
