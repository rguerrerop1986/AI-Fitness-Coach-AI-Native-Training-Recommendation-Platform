from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.training.models import ExerciseSet, WorkoutExercise, WorkoutSession


class WorkoutSessionService:
    """Domain logic for hybrid workout sessions."""

    @staticmethod
    def _assert_editable(session: WorkoutSession) -> None:
        if session.status == WorkoutSession.Status.COMPLETED:
            raise ValidationError("This workout session is already completed.")

    @staticmethod
    def get_user_session(*, user, session_id: int) -> WorkoutSession:
        try:
            return (
                WorkoutSession.objects.select_related("user")
                .prefetch_related("exercises__sets")
                .get(id=session_id, user=user)
            )
        except WorkoutSession.DoesNotExist as exc:
            raise ValidationError("Workout session not found.") from exc

    @transaction.atomic
    def create_session(self, *, user, payload: dict) -> WorkoutSession:
        return WorkoutSession.objects.create(user=user, **payload)

    @transaction.atomic
    def update_session(self, *, session: WorkoutSession, payload: dict) -> WorkoutSession:
        self._assert_editable(session)
        for field, value in payload.items():
            setattr(session, field, value)
        session.save()
        return session

    @transaction.atomic
    def add_exercise(self, *, session: WorkoutSession, payload: dict) -> WorkoutExercise:
        self._assert_editable(session)
        payload = dict(payload)
        next_order = (
            WorkoutExercise.objects.filter(workout_session=session).aggregate(max_order=Max("order"))["max_order"]
            or 0
        ) + 1
        order = payload.pop("order", None) or next_order
        return WorkoutExercise.objects.create(workout_session=session, order=order, **payload)

    @transaction.atomic
    def update_exercise(self, *, session: WorkoutSession, exercise_id: int, payload: dict) -> WorkoutExercise:
        self._assert_editable(session)
        try:
            exercise = WorkoutExercise.objects.get(id=exercise_id, workout_session=session)
        except WorkoutExercise.DoesNotExist as exc:
            raise ValidationError("Workout exercise not found.") from exc
        for field, value in payload.items():
            setattr(exercise, field, value)
        exercise.save()
        return exercise

    @transaction.atomic
    def delete_exercise(self, *, session: WorkoutSession, exercise_id: int) -> None:
        self._assert_editable(session)
        deleted, _ = WorkoutExercise.objects.filter(id=exercise_id, workout_session=session).delete()
        if not deleted:
            raise ValidationError("Workout exercise not found.")

    @transaction.atomic
    def add_set(self, *, session: WorkoutSession, exercise_id: int, payload: dict) -> ExerciseSet:
        self._assert_editable(session)
        payload = dict(payload)
        try:
            exercise = WorkoutExercise.objects.get(id=exercise_id, workout_session=session)
        except WorkoutExercise.DoesNotExist as exc:
            raise ValidationError("Workout exercise not found.") from exc
        next_set_number = (
            ExerciseSet.objects.filter(workout_exercise=exercise).aggregate(max_set=Max("set_number"))["max_set"] or 0
        ) + 1
        set_number = payload.pop("set_number", None) or next_set_number
        return ExerciseSet.objects.create(
            workout_exercise=exercise,
            set_number=set_number,
            **payload,
        )

    @transaction.atomic
    def update_set(self, *, session: WorkoutSession, exercise_id: int, set_id: int, payload: dict) -> ExerciseSet:
        self._assert_editable(session)
        try:
            target_set = ExerciseSet.objects.get(
                id=set_id,
                workout_exercise_id=exercise_id,
                workout_exercise__workout_session=session,
            )
        except ExerciseSet.DoesNotExist as exc:
            raise ValidationError("Exercise set not found.") from exc
        for field, value in payload.items():
            setattr(target_set, field, value)
        target_set.save()
        return target_set

    @transaction.atomic
    def delete_set(self, *, session: WorkoutSession, exercise_id: int, set_id: int) -> None:
        self._assert_editable(session)
        deleted, _ = ExerciseSet.objects.filter(
            id=set_id,
            workout_exercise_id=exercise_id,
            workout_exercise__workout_session=session,
        ).delete()
        if not deleted:
            raise ValidationError("Exercise set not found.")

    @transaction.atomic
    def complete_session(self, *, session: WorkoutSession) -> WorkoutSession:
        self._assert_editable(session)

        exercises_qs = WorkoutExercise.objects.filter(workout_session=session)
        sets_qs = ExerciseSet.objects.filter(workout_exercise__workout_session=session)

        total_exercises = exercises_qs.count()
        total_sets = sets_qs.count()
        total_reps = sets_qs.aggregate(total_reps=Sum("reps"))["total_reps"] or 0

        total_volume = Decimal("0")
        for s in sets_qs:
            if s.weight_kg is not None and s.reps is not None:
                total_volume += s.weight_kg * Decimal(s.reps)

        session.status = WorkoutSession.Status.COMPLETED
        session.completed_at = timezone.now()
        session.total_exercises = total_exercises
        session.total_sets = total_sets
        session.total_reps = total_reps
        session.total_volume = total_volume
        session.save()
        return session


def build_workout_ai_payload(session: WorkoutSession) -> dict:
    """Small helper to produce a summarized payload for AI features."""
    exercises_payload = []
    for exercise in session.exercises.all().order_by("order", "id"):
        sets_payload = []
        for item in exercise.sets.all().order_by("set_number", "id"):
            sets_payload.append(
                {
                    "set_number": item.set_number,
                    "reps": item.reps,
                    "weight_kg": float(item.weight_kg) if item.weight_kg is not None else None,
                    "intensity": item.intensity,
                    "rest_seconds": item.rest_seconds,
                }
            )
        exercises_payload.append(
            {
                "exercise_name": exercise.exercise_name,
                "order": exercise.order,
                "intensity": exercise.intensity,
                "notes": exercise.notes,
                "sets": sets_payload,
            }
        )

    return {
        "session_id": session.id,
        "session_date": session.session_date.isoformat(),
        "workout_type": session.workout_type,
        "status": session.status,
        "video_name": session.video_name,
        "title": session.title,
        "notes": session.notes,
        "totals": {
            "total_exercises": session.total_exercises,
            "total_sets": session.total_sets,
            "total_reps": session.total_reps,
            "total_volume": float(session.total_volume or 0),
        },
        "exercises": exercises_payload,
    }
