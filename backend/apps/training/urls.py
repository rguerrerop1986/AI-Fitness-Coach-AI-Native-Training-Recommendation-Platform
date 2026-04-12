from django.urls import path
from . import views

app_name = "training"

urlpatterns = [
    path("checkins/", views.DailyCheckInListCreateView.as_view(), name="checkin-list-create"),
    path("checkins/daily/", views.DailyCheckInDailyUpsertView.as_view(), name="checkin-daily-upsert"),
    path(
        "recommendations/generate/",
        views.GenerateAdaptiveRecommendationView.as_view(),
        name="recommendation-generate",
    ),
    path(
        "recommendations/generate-legacy/",
        views.GenerateRecommendationView.as_view(),
        name="recommendation-generate-legacy",
    ),
    path(
        "recommendations/today/",
        views.TodayRecommendationView.as_view(),
        name="recommendation-today",
    ),
    path(
        "recommendations/history/",
        views.RecommendationHistoryView.as_view(),
        name="recommendation-history",
    ),
    path("workout-logs/", views.WorkoutLogListCreateView.as_view(), name="workout-log-list-create"),
    path("workouts/complete/", views.CompleteWorkoutView.as_view(), name="workout-complete"),
    path("readiness/today/", views.TodayReadinessView.as_view(), name="readiness-today"),
    path(
        "workout-feedback/analyze/",
        views.WorkoutFeedbackAnalyzeView.as_view(),
        name="workout-feedback-analyze",
    ),
    path("workout-sessions/", views.WorkoutSessionCreateView.as_view(), name="workout-session-create"),
    path("workout-sessions/<int:session_id>/", views.WorkoutSessionDetailView.as_view(), name="workout-session-detail"),
    path(
        "workout-sessions/<int:session_id>/exercises/",
        views.WorkoutSessionExerciseListCreateView.as_view(),
        name="workout-session-exercise-create",
    ),
    path(
        "workout-sessions/<int:session_id>/exercises/<int:exercise_id>/",
        views.WorkoutSessionExerciseDetailView.as_view(),
        name="workout-session-exercise-detail",
    ),
    path(
        "workout-sessions/<int:session_id>/exercises/<int:exercise_id>/sets/",
        views.WorkoutSessionSetListCreateView.as_view(),
        name="workout-session-set-create",
    ),
    path(
        "workout-sessions/<int:session_id>/exercises/<int:exercise_id>/sets/<int:set_id>/",
        views.WorkoutSessionSetDetailView.as_view(),
        name="workout-session-set-detail",
    ),
    path(
        "workout-sessions/<int:session_id>/complete/",
        views.WorkoutSessionCompleteView.as_view(),
        name="workout-session-complete",
    ),
    path(
        "workout-sessions/<int:session_id>/ai-payload/",
        views.WorkoutSessionAIPayloadView.as_view(),
        name="workout-session-ai-payload",
    ),
]
