from django.contrib import admin
from .models import TrainingVideo, DailyCheckIn, WorkoutLog, TrainingRecommendation


@admin.register(TrainingVideo)
class TrainingVideoAdmin(admin.ModelAdmin):
    list_display = ["name", "program", "category", "difficulty", "duration_minutes", "is_active"]
    list_filter = ["category", "difficulty", "is_active", "explosive"]


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "energy_level", "sleep_quality", "joint_pain", "created_at"]
    list_filter = ["date", "joint_pain"]
    search_fields = ["user__email", "notes"]


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "video", "completed", "rpe", "pain_during_workout", "created_at"]
    list_filter = ["date", "completed", "pain_during_workout"]
    raw_id_fields = ["user", "video"]


@admin.register(TrainingRecommendation)
class TrainingRecommendationAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "recommended_video", "recommendation_type", "created_at"]
    list_filter = ["date", "recommendation_type"]
    raw_id_fields = ["user", "recommended_video"]
