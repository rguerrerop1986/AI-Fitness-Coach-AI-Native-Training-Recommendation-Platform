"""
Serializers for Internal API responses (read-only representation for MCP).
"""
from rest_framework import serializers
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise


def exercise_summary(exercise):
    if not exercise:
        return None
    return {
        'id': exercise.id,
        'name': exercise.name,
        'intensity': getattr(exercise, 'intensity', 5),
        'tags': getattr(exercise, 'tags', []),
        'muscle_group': exercise.muscle_group,
    }


class InternalTrainingLogSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    date = serializers.DateField()
    suggested_exercise = serializers.SerializerMethodField()
    executed_exercise = serializers.SerializerMethodField()
    execution_status = serializers.CharField()
    rpe = serializers.IntegerField(allow_null=True)
    energy_level = serializers.IntegerField(allow_null=True)
    pain_level = serializers.IntegerField(allow_null=True)
    notes = serializers.CharField()
    recommendation_version = serializers.CharField(allow_blank=True)
    recommendation_meta = serializers.JSONField(allow_null=True)
    recommendation_confidence = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)

    def get_suggested_exercise(self, obj):
        return exercise_summary(obj.suggested_exercise)

    def get_executed_exercise(self, obj):
        return exercise_summary(obj.executed_exercise)


class InternalExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'muscle_group', 'equipment_type', 'difficulty', 'intensity', 'tags', 'instructions', 'image_url', 'video_url']
