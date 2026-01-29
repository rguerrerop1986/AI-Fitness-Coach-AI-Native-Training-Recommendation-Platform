from rest_framework import serializers
from .models import CheckIn, TrainingLog, DietLog


# ---- Exercise summary for nested read (TrainingLog) ----
def _exercise_summary(exercise):
    if not exercise:
        return None
    return {'id': exercise.id, 'name': exercise.name, 'image_url': exercise.image_url or ''}


class TrainingLogSerializer(serializers.ModelSerializer):
    suggested_exercise_summary = serializers.SerializerMethodField()
    executed_exercise_summary = serializers.SerializerMethodField()

    def get_suggested_exercise_summary(self, obj):
        return _exercise_summary(obj.suggested_exercise)

    def get_executed_exercise_summary(self, obj):
        return _exercise_summary(obj.executed_exercise)

    class Meta:
        model = TrainingLog
        fields = [
            'id', 'client', 'plan_cycle', 'coach', 'date',
            'suggested_exercise', 'executed_exercise',
            'suggested_exercise_summary', 'executed_exercise_summary',
            'execution_status', 'duration_minutes', 'rpe', 'energy_level',
            'pain_level', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rpe(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('RPE must be between 1 and 10.')
        return value

    def validate_energy_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Energy level must be between 1 and 10.')
        return value

    def validate_pain_level(self, value):
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError('Pain level must be between 0 and 10.')
        return value


class DietLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietLog
        fields = [
            'id', 'client', 'plan_cycle', 'coach', 'date',
            'adherence_percent', 'calories_estimate_kcal', 'protein_estimate_g',
            'carbs_estimate_g', 'fats_estimate_g',
            'hunger_level', 'cravings_level', 'digestion_quality', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_adherence_percent(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError('Adherence must be between 0 and 100.')
        return value

    def validate_hunger_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Hunger level must be between 1 and 10.')
        return value

    def validate_cravings_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Cravings level must be between 1 and 10.')
        return value

    def validate_digestion_quality(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Digestion quality must be between 1 and 10.')
        return value


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
