from django.contrib import admin
from .models import (
    CompletedWorkout,
    DailyCheckIn,
    TrainingRecommendation,
    TrainingRecommendationExercise,
    TrainingVideo,
    WorkoutLog,
)


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
    list_display = [
        "user",
        "date",
        "recommendation_type",
        "intensity_level",
        "duration_minutes",
        "readiness_score",
        "created_at",
    ]
    list_filter = ["date", "recommendation_type"]
    raw_id_fields = ["user", "checkin", "recommended_exercise", "recommended_video"]


@admin.register(TrainingRecommendationExercise)
class TrainingRecommendationExerciseAdmin(admin.ModelAdmin):
    list_display = ["recommendation", "exercise", "sets", "reps", "rest_seconds", "position"]
    raw_id_fields = ["recommendation", "exercise"]


@admin.register(CompletedWorkout)
class CompletedWorkoutAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "workout_type", "completed", "perceived_exertion", "created_at"]
    list_filter = ["date", "completed", "workout_type"]
    raw_id_fields = ["user", "recommendation"]
