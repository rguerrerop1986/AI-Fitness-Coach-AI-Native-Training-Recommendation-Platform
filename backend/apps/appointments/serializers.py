from datetime import datetime
import zoneinfo
from rest_framework import serializers
from django.utils.dateparse import parse_datetime
from django.utils import timezone as django_tz
from .models import Appointment
from apps.clients.serializers import ClientSerializer

# Business timezone: all appointment times are in Mexico City
APPOINTMENT_TZ = zoneinfo.ZoneInfo('America/Mexico_City')


def parse_scheduled_at_as_local(value):
    """
    Parse scheduled_at from API. If the string has no timezone (naive),
    interpret as America/Mexico_City and return aware UTC for storage.
    """
    if value is None:
        return value
    if isinstance(value, datetime):
        dt = value
    else:
        dt = parse_datetime(str(value))
    if dt is None:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=APPOINTMENT_TZ)
    return dt.astimezone(django_tz.utc)


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model (coach view - full CRUD)."""
    client_detail = ClientSerializer(source='client', read_only=True)
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'client', 'client_detail', 'coach', 'coach_name',
            'scheduled_at', 'duration_minutes', 'status', 'notes',
            'price', 'currency', 'payment_status', 'payment_method',
            'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['coach', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        if 'scheduled_at' in internal and internal['scheduled_at'] is not None:
            internal['scheduled_at'] = parse_scheduled_at_as_local(internal['scheduled_at'])
        return internal

    def validate(self, attrs):
        payment_status = attrs.get(
            'payment_status',
            self.instance.payment_status if self.instance else Appointment.PaymentStatus.UNPAID
        )
        status = attrs.get(
            'status',
            self.instance.status if self.instance else Appointment.Status.SCHEDULED
        )
        if payment_status == Appointment.PaymentStatus.PAID and status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError({
                'payment_status': 'Appointment must be COMPLETED before marking as PAID.'
            })
        if payment_status == Appointment.PaymentStatus.PAID:
            payment_method = attrs.get(
                'payment_method',
                self.instance.payment_method if self.instance else None
            )
            if not payment_method:
                raise serializers.ValidationError({
                    'payment_method': 'Payment method is required when payment status is PAID.'
                })
        return attrs
    
    def create(self, validated_data):
        """Set coach to current user on create."""
        validated_data['coach'] = self.context['request'].user
        return super().create(validated_data)


class ClientAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model (client view - read-only)."""
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'coach_name', 'scheduled_at', 'duration_minutes',
            'status', 'notes', 'price', 'currency', 'payment_status',
            'payment_method', 'paid_at', 'created_at'
        ]
        read_only_fields = fields  # All fields are read-only for clients
