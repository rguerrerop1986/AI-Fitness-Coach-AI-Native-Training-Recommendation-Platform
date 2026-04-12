from django.contrib import admin
from .models import (
    CompletedWorkout,
    DailyCheckIn,
    ExerciseSet,
    TrainingRecommendation,
    TrainingRecommendationExercise,
    TrainingVideo,
    WorkoutExercise,
    WorkoutLog,
    WorkoutSession,
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


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "session_date",
        "workout_type",
        "status",
        "total_exercises",
        "total_sets",
        "total_reps",
        "total_volume",
        "completed_at",
    ]
    list_filter = ["workout_type", "status", "session_date"]
    raw_id_fields = ["user"]


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ["workout_session", "exercise_name", "order", "intensity"]
    list_filter = ["workout_session__workout_type"]
    raw_id_fields = ["workout_session"]


@admin.register(ExerciseSet)
class ExerciseSetAdmin(admin.ModelAdmin):
    list_display = ["workout_exercise", "set_number", "reps", "weight_kg", "intensity", "rest_seconds"]
    raw_id_fields = ["workout_exercise"]
