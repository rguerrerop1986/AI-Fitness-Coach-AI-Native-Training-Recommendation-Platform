from rest_framework import serializers
from .models import CheckIn


class CheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = [
            'id', 'client', 'date', 'weight_kg', 'body_fat_pct',
            'chest_cm', 'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'rpe', 'fatigue', 'diet_adherence', 'workout_adherence', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CheckInCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating check-ins without requiring client field."""
    class Meta:
        model = CheckIn
        fields = [
            'date', 'weight_kg', 'body_fat_pct',
            'chest_cm', 'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'rpe', 'fatigue', 'diet_adherence', 'workout_adherence', 'notes'
        ]
