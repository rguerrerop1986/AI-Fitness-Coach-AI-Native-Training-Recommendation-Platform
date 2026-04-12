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
    CompletedWorkoutSerializer,
    DailyCheckInSerializer,
    DailyCheckInCreateSerializer,
    DailyCheckInUpsertSerializer,
    ExerciseSetCreateSerializer,
    ExerciseSetSerializer,
    ExerciseSetUpdateSerializer,
    GenerateRecommendationRequestSerializer,
    TrainingRecommendationSerializer,
    WorkoutExerciseCreateSerializer,
    WorkoutExerciseSerializer,
    WorkoutExerciseUpdateSerializer,
    WorkoutLogSerializer,
    WorkoutLogCreateSerializer,
    WorkoutSessionCreateSerializer,
    WorkoutSessionSerializer,
    WorkoutSessionUpdateSerializer,
    GenerateRecommendationInputSerializer,
    WorkoutFeedbackAnalyzeInputSerializer,
)
from .models import CompletedWorkout, TrainingRecommendation
from .services.adaptive_recommendation_service import AdaptiveRecommendationService
from .services.readiness_service import ReadinessService
from .services.recommendation_service import generate_recommendation
from .services.feedback_analysis import analyze_workout_feedback
from .services.workout_session_service import WorkoutSessionService, build_workout_ai_payload


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


class DailyCheckInDailyUpsertView(APIView):
    """POST /api/checkins/daily/ - create or update today's check-in."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DailyCheckInUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        checkin, created = DailyCheckIn.objects.update_or_create(
            user=request.user,
            date=serializer.validated_data["date"],
            defaults=serializer.validated_data,
        )
        return Response(
            DailyCheckInSerializer(checkin).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class GenerateAdaptiveRecommendationView(APIView):
    """POST /api/training/recommendations/generate/ - deterministic adaptive recommendation."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_date = serializer.validated_data.get("date") or request.query_params.get("date")
        if not target_date:
            from django.utils import timezone

            target_date = timezone.localdate()
        if isinstance(target_date, str):
            from datetime import date as date_cls

            target_date = date_cls.fromisoformat(target_date)
        regenerate = serializer.validated_data.get("regenerate", True)
        service = AdaptiveRecommendationService()
        recommendation, generated = service.generate_for_date(
            request.user,
            target_date=target_date,
            regenerate=regenerate,
        )
        data = TrainingRecommendationSerializer(recommendation).data
        data["generation_policy"] = "regenerated" if generated else "returned_existing"
        return Response(data, status=status.HTTP_200_OK)


class TodayRecommendationView(APIView):
    """GET /api/training/recommendations/today/."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone

        recommendation = TrainingRecommendation.objects.filter(
            user=request.user,
            date=timezone.localdate(),
        ).first()
        if not recommendation:
            return Response({"detail": "No recommendation for today."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TrainingRecommendationSerializer(recommendation).data, status=status.HTTP_200_OK)


class RecommendationHistoryView(ListCreateAPIView):
    """GET /api/training/recommendations/history/ - paginated history."""

    permission_classes = [IsAuthenticated]
    serializer_class = TrainingRecommendationSerializer

    def get_queryset(self):
        return TrainingRecommendation.objects.filter(user=self.request.user).order_by("-date", "-created_at")

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CompleteWorkoutView(APIView):
    """POST /api/training/workouts/complete/."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompletedWorkoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workout = serializer.save(user=request.user)
        return Response(CompletedWorkoutSerializer(workout).data, status=status.HTTP_201_CREATED)


class TodayReadinessView(APIView):
    """GET /api/training/readiness/today/ - readiness analysis without persistence."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone

        checkin = DailyCheckIn.objects.filter(user=request.user, date=timezone.localdate()).first()
        if not checkin:
            return Response({"detail": "No daily check-in for today."}, status=status.HTTP_404_NOT_FOUND)
        analysis = ReadinessService().analyze(checkin)
        return Response(analysis.asdict(), status=status.HTTP_200_OK)


class WorkoutSessionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkoutSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = WorkoutSessionService().create_session(user=request.user, payload=serializer.validated_data)
        return Response(WorkoutSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class WorkoutSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        return Response(WorkoutSessionSerializer(session).data, status=status.HTTP_200_OK)

    def patch(self, request, session_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        serializer = WorkoutSessionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = WorkoutSessionService().update_session(session=session, payload=serializer.validated_data)
        return Response(WorkoutSessionSerializer(updated).data, status=status.HTTP_200_OK)


class WorkoutSessionExerciseListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        serializer = WorkoutExerciseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exercise = WorkoutSessionService().add_exercise(session=session, payload=serializer.validated_data)
        return Response(WorkoutExerciseSerializer(exercise).data, status=status.HTTP_201_CREATED)


class WorkoutSessionExerciseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, session_id: int, exercise_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        serializer = WorkoutExerciseUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exercise = WorkoutSessionService().update_exercise(
            session=session,
            exercise_id=exercise_id,
            payload=serializer.validated_data,
        )
        return Response(WorkoutExerciseSerializer(exercise).data, status=status.HTTP_200_OK)

    def delete(self, request, session_id: int, exercise_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        WorkoutSessionService().delete_exercise(session=session, exercise_id=exercise_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutSessionSetListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int, exercise_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        serializer = ExerciseSetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exercise_set = WorkoutSessionService().add_set(
            session=session,
            exercise_id=exercise_id,
            payload=serializer.validated_data,
        )
        return Response(ExerciseSetSerializer(exercise_set).data, status=status.HTTP_201_CREATED)


class WorkoutSessionSetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, session_id: int, exercise_id: int, set_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        serializer = ExerciseSetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exercise_set = WorkoutSessionService().update_set(
            session=session,
            exercise_id=exercise_id,
            set_id=set_id,
            payload=serializer.validated_data,
        )
        return Response(ExerciseSetSerializer(exercise_set).data, status=status.HTTP_200_OK)

    def delete(self, request, session_id: int, exercise_id: int, set_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        WorkoutSessionService().delete_set(session=session, exercise_id=exercise_id, set_id=set_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkoutSessionCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        completed = WorkoutSessionService().complete_session(session=session)
        return Response(WorkoutSessionSerializer(completed).data, status=status.HTTP_200_OK)


class WorkoutSessionAIPayloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        session = WorkoutSessionService.get_user_session(user=request.user, session_id=session_id)
        return Response(build_workout_ai_payload(session), status=status.HTTP_200_OK)
