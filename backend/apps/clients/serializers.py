from rest_framework import serializers
from .models import Client, Measurement


class MeasurementSerializer(serializers.ModelSerializer):
    """Serializer for client measurements."""
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'date', 'weight_kg', 'body_fat_pct', 'chest_cm', 
            'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for client data."""
    measurements = MeasurementSerializer(many=True, read_only=True)
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'date_of_birth', 
            'age', 'sex', 'email', 'phone', 'height_cm', 'initial_weight_kg',
            'notes', 'consent_checkbox', 'emergency_contact', 'is_active',
            'measurements', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating clients."""
    
    class Meta:
        model = Client
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'sex', 'email', 
            'phone', 'height_cm', 'initial_weight_kg', 'notes', 
            'consent_checkbox', 'emergency_contact'
        ]
    
    def validate_consent_checkbox(self, value):
        if not value:
            raise serializers.ValidationError("Consent checkbox must be checked.")
        return value


class ClientMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for creating measurements for a specific client."""
    
    class Meta:
        model = Measurement
        fields = [
            'date', 'weight_kg', 'body_fat_pct', 'chest_cm', 
            'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm'
        ]
    
    def create(self, validated_data):
        client_id = self.context['client_id']
        validated_data['client_id'] = client_id
        return super().create(validated_data)
