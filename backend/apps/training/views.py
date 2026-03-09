"""
API views for training: check-ins, recommendations, workout logs, feedback analysis.
"""
from django.db import IntegrityError

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView

from .models import DailyCheckIn, WorkoutLog
from .serializers import (
    DailyCheckInSerializer,
    DailyCheckInCreateSerializer,
    WorkoutLogSerializer,
    WorkoutLogCreateSerializer,
    GenerateRecommendationInputSerializer,
    WorkoutFeedbackAnalyzeInputSerializer,
)
from .services.recommendation_service import generate_recommendation
from .services.feedback_analysis import analyze_workout_feedback


class DailyCheckInListCreateView(ListCreateAPIView):
    """POST /api/training/checkins/ - create; GET - list (filtered by user)."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DailyCheckInCreateSerializer
        return DailyCheckInSerializer

    def get_queryset(self):
        return DailyCheckIn.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        date = serializer.validated_data["date"]
        existing = DailyCheckIn.objects.filter(user=user, date=date).first()
        if existing:
            for attr, value in serializer.validated_data.items():
                setattr(existing, attr, value)
            existing.save()
            return Response(
                DailyCheckInSerializer(existing).data,
                status=status.HTTP_200_OK,
            )
        try:
            self.perform_create(serializer)
        except IntegrityError:
            # Race condition or duplicate: update existing and return 200
            existing = DailyCheckIn.objects.get(user=user, date=date)
            for attr, value in serializer.validated_data.items():
                setattr(existing, attr, value)
            existing.save()
            return Response(
                DailyCheckInSerializer(existing).data,
                status=status.HTTP_200_OK,
            )
        instance = serializer.instance
        return Response(
            DailyCheckInSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


class GenerateRecommendationView(APIView):
    """POST /api/training/recommendations/generate/ - body: { "date": "YYYY-MM-DD" }. Response contract: GenerateRecommendationResponseSerializer (date, recommendation_plan, persisted_recommendation_id, readiness_score, warnings, error, optional recommended_exercise). 200 when valid payload; non-200 only for validation or unrecoverable failure."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = GenerateRecommendationInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        for_date = ser.validated_data["date"]
        result = generate_recommendation(request.user, for_date)
        # Return 200 whenever we have a valid recommendation payload (including fallbacks)
        if result.get("recommendation_plan") is not None:
            return Response(result, status=status.HTTP_200_OK)
        # Unrecoverable: no plan (e.g. graph/persistence failed without fallback)
        return Response(
            result,
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class WorkoutLogListCreateView(ListCreateAPIView):
    """POST /api/training/workout-logs/ - create; GET - list (filtered by user)."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkoutLogCreateSerializer
        return WorkoutLogSerializer

    def get_queryset(self):
        return WorkoutLog.objects.filter(user=self.request.user).select_related("video").order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response(
            WorkoutLogSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


class WorkoutFeedbackAnalyzeView(APIView):
    """POST /api/training/workout-feedback/analyze/ - analyze feedback, return summary, coach_comment, tomorrow_hint."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = WorkoutFeedbackAnalyzeInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if data.get("workout_log_id") is not None:
            log = WorkoutLog.objects.filter(
                user=request.user,
                pk=data["workout_log_id"],
            ).select_related("video").first()
            if not log:
                return Response(
                    {"detail": "Workout log not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            video_name = log.video.name if log.video else "Unknown"
            result = analyze_workout_feedback(
                video_name=video_name,
                completed=log.completed,
                rpe=log.rpe,
                satisfaction=log.satisfaction,
                felt_strong=log.felt_strong,
                felt_drained=log.felt_drained,
                recovery_fast=log.recovery_fast,
                pain_during_workout=log.pain_during_workout,
                pain_notes=log.pain_notes or "",
                body_feedback=log.body_feedback or "",
                emotional_feedback=log.emotional_feedback or "",
            )
        else:
            result = analyze_workout_feedback(
                video_name=data.get("video_name") or "Workout",
                completed=data.get("completed", True),
                rpe=data.get("rpe"),
                satisfaction=data.get("satisfaction"),
                felt_strong=data.get("felt_strong"),
                felt_drained=data.get("felt_drained"),
                recovery_fast=data.get("recovery_fast"),
                pain_during_workout=data.get("pain_during_workout", False),
                pain_notes=data.get("pain_notes") or "",
                body_feedback=data.get("body_feedback") or "",
                emotional_feedback=data.get("emotional_feedback") or "",
            )
        return Response(result, status=status.HTTP_200_OK)
