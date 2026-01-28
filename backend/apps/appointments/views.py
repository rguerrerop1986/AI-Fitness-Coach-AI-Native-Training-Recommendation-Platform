from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Appointment
from .serializers import AppointmentSerializer, ClientAppointmentSerializer
from apps.common.permissions import IsCoach, IsClient
from apps.common.utils import get_client_from_user

class AppointmentViewSet(viewsets.ModelViewSet):
    """ViewSet for appointment management (coach only - full CRUD)."""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsCoach]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status', 'client', 'coach']
    ordering_fields = ['scheduled_at', 'created_at', 'price']
    ordering = ['-scheduled_at']
    
    def get_queryset(self):
        """Filter appointments by coach or client if specified."""
        queryset = super().get_queryset()
        
        # Filter by client_id if provided
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by coach (current user)
        queryset = queryset.filter(coach=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def mark_completed(self, request, pk=None):
        """Mark appointment as completed."""
        appointment = self.get_object()
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_paid(self, request, pk=None):
        """Mark appointment as paid."""
        appointment = self.get_object()
        
        # Validate that appointment is completed
        if appointment.status != Appointment.Status.COMPLETED:
            return Response({
                'error': 'Appointment must be COMPLETED before marking as PAID.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = request.data.get('payment_method')
        if not payment_method:
            return Response({
                'error': 'Payment method is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        appointment.payment_status = Appointment.PaymentStatus.PAID
        appointment.payment_method = payment_method
        appointment.paid_at = timezone.now()
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel an appointment."""
        appointment = self.get_object()
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)


class ClientAppointmentView(APIView):
    """View for clients to see their own appointments (read-only)."""
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        """Get all appointments for the current client."""
        client = get_client_from_user(request.user)
        if not client:
            return Response({
                'error': 'Client profile not found. Please contact your coach.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        appointments = Appointment.objects.filter(client=client).order_by('-scheduled_at')
        
        # Separate upcoming and past appointments
        now = timezone.now()
        upcoming = appointments.filter(scheduled_at__gte=now)
        past = appointments.filter(scheduled_at__lt=now)
        
        serializer = ClientAppointmentSerializer(appointments, many=True)
        upcoming_serializer = ClientAppointmentSerializer(upcoming, many=True)
        past_serializer = ClientAppointmentSerializer(past, many=True)
        
        return Response({
            'all': serializer.data,
            'upcoming': upcoming_serializer.data,
            'past': past_serializer.data
        })
