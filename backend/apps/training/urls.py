from django.urls import path
from . import views

app_name = "training"

urlpatterns = [
    path("checkins/", views.DailyCheckInListCreateView.as_view(), name="checkin-list-create"),
    path(
        "recommendations/generate/",
        views.GenerateRecommendationView.as_view(),
        name="recommendation-generate",
    ),
    path("workout-logs/", views.WorkoutLogListCreateView.as_view(), name="workout-log-list-create"),
    path(
        "workout-feedback/analyze/",
        views.WorkoutFeedbackAnalyzeView.as_view(),
        name="workout-feedback-analyze",
    ),
]
