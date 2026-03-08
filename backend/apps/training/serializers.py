"""
Serializers for training module: check-ins, workout logs, recommendations, feedback.
"""
from rest_framework import serializers

from .models import DailyCheckIn, TrainingRecommendation, TrainingVideo, WorkoutLog


class TrainingVideoListSerializer(serializers.ModelSerializer):
    """Minimal video for recommendation response and lists."""

    class Meta:
        model = TrainingVideo
        fields = ["id", "name", "program", "category", "difficulty", "duration_minutes"]


class DailyCheckInSerializer(serializers.ModelSerializer):
    """Full check-in read/write. User is set from request."""

    class Meta:
        model = DailyCheckIn
        fields = [
            "id",
            "user",
            "date",
            "hours_sleep",
            "sleep_quality",
            "energy_level",
            "motivation_level",
            "mood",
            "soreness_legs",
            "soreness_arms",
            "soreness_core",
            "soreness_shoulders",
            "joint_pain",
            "pain_notes",
            "did_gym_today",
            "did_gym_yesterday",
            "gym_focus",
            "wants_intensity",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_sleep_quality(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_energy_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_motivation_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_legs(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_arms(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_core(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_shoulders(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_hours_sleep(self, value):
        if value is not None and (float(value) < 0 or float(value) > 24):
            raise serializers.ValidationError("Must be between 0 and 24.")
        return value


class DailyCheckInCreateSerializer(serializers.ModelSerializer):
    """Create check-in; user from request, date and other fields from body."""

    class Meta:
        model = DailyCheckIn
        fields = [
            "date",
            "hours_sleep",
            "sleep_quality",
            "energy_level",
            "motivation_level",
            "mood",
            "soreness_legs",
            "soreness_arms",
            "soreness_core",
            "soreness_shoulders",
            "joint_pain",
            "pain_notes",
            "did_gym_today",
            "did_gym_yesterday",
            "gym_focus",
            "wants_intensity",
            "notes",
        ]

    def validate_date(self, value):
        if value is None:
            raise serializers.ValidationError("date is required.")
        return value

    def validate_sleep_quality(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_energy_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_legs(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_arms(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_core(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_soreness_shoulders(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_hours_sleep(self, value):
        if value is not None and (float(value) < 0 or float(value) > 24):
            raise serializers.ValidationError("Must be between 0 and 24.")
        return value


class WorkoutLogSerializer(serializers.ModelSerializer):
    """Workout log with optional video summary."""

    video_summary = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutLog
        fields = [
            "id",
            "user",
            "date",
            "video",
            "video_summary",
            "completed",
            "paused",
            "rpe",
            "breathing",
            "sweat_level",
            "satisfaction",
            "performance",
            "felt_strong",
            "felt_drained",
            "recovery_fast",
            "pain_during_workout",
            "pain_notes",
            "body_feedback",
            "emotional_feedback",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_video_summary(self, obj):
        if not obj.video:
            return None
        return {"id": obj.video.id, "name": obj.video.name, "category": obj.video.category}

    def validate_rpe(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("RPE must be between 1 and 10.")
        return value

    def validate_sweat_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value

    def validate_satisfaction(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Must be between 1 and 10.")
        return value


class WorkoutLogCreateSerializer(serializers.ModelSerializer):
    """Create workout log; user from request."""

    class Meta:
        model = WorkoutLog
        fields = [
            "date",
            "video",
            "completed",
            "paused",
            "rpe",
            "breathing",
            "sweat_level",
            "satisfaction",
            "performance",
            "felt_strong",
            "felt_drained",
            "recovery_fast",
            "pain_during_workout",
            "pain_notes",
            "body_feedback",
            "emotional_feedback",
        ]

    def validate_rpe(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("RPE must be between 1 and 10.")
        return value


class GenerateRecommendationInputSerializer(serializers.Serializer):
    """Input for POST /api/training/recommendations/generate/."""

    date = serializers.DateField(required=True)


class RecommendationResponseSerializer(serializers.Serializer):
    """Output shape for recommendation generate endpoint."""

    date = serializers.CharField()
    recommended_video = serializers.DictField(allow_null=True)
    recommendation_type = serializers.CharField()
    reasoning_summary = serializers.CharField()
    warnings = serializers.CharField()
    coach_message = serializers.CharField()


class WorkoutFeedbackAnalyzeInputSerializer(serializers.Serializer):
    """Input for POST /api/training/workout-feedback/analyze/. Can be log id or raw payload."""

    workout_log_id = serializers.IntegerField(required=False, allow_null=True)
    # Or pass fields directly for analysis without saving
    video_name = serializers.CharField(required=False, allow_blank=True)
    completed = serializers.BooleanField(required=False, default=True)
    rpe = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=10)
    satisfaction = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=10)
    felt_strong = serializers.BooleanField(required=False, allow_null=True)
    felt_drained = serializers.BooleanField(required=False, allow_null=True)
    recovery_fast = serializers.BooleanField(required=False, allow_null=True)
    pain_during_workout = serializers.BooleanField(required=False, default=False)
    pain_notes = serializers.CharField(required=False, allow_blank=True, default="")
    body_feedback = serializers.CharField(required=False, allow_blank=True, default="")
    emotional_feedback = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs.get("workout_log_id") is not None:
            return attrs
        if not attrs.get("video_name"):
            raise serializers.ValidationError(
                "Either workout_log_id or video_name must be provided."
            )
        return attrs
