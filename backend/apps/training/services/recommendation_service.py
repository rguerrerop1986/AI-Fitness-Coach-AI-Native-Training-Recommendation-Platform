"""
Orchestrates daily recommendation: check-in -> history -> readiness -> candidates (Exercise) -> context -> OpenAI -> persist.
"""
from datetime import date
from typing import Any, Dict

from django.db import transaction

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation
from apps.training.selectors import (
    get_checkin_for_date,
    get_recent_recommendations,
    get_recent_workout_logs,
)
from apps.training.services.exercise_selector import get_candidate_exercises
from apps.training.services.openai_coach import recommend_workout_from_candidates
from apps.training.services.readiness import evaluate_readiness
from apps.training.services.recommendation_context import build_recommendation_context


def _exercise_to_response(ex: Exercise) -> Dict[str, Any]:
    return {
        "id": ex.id,
        "name": ex.name,
        "muscle_group": ex.muscle_group,
        "difficulty": ex.difficulty,
        "intensity": ex.intensity,
        "tags": list(ex.tags) if ex.tags else [],
    }


def generate_recommendation(user, for_date: date) -> Dict[str, Any]:
    """
    Generate (or reuse) a training recommendation for the user on the given date.
    - Loads check-in and recent workout logs and recommendations.
    - Evaluates readiness (deterministic).
    - Selects 3-5 candidate exercises from catalogs.Exercise.
    - Builds structured context (history, feedbacks, previous recommendations).
    - Calls OpenAI to pick one exercise; persists TrainingRecommendation with recommended_exercise.
    Returns a dict with date, recommended_exercise, recommendation_type, etc.
    """
    check_in = get_checkin_for_date(user, for_date)
    recent_logs = list(get_recent_workout_logs(user, days=14, before_date=for_date))
    recent_recs = list(get_recent_recommendations(user, days=14, before_date=for_date))

    readiness = evaluate_readiness(check_in, recent_logs, for_date)
    candidates = get_candidate_exercises(readiness, check_in, limit=5)

    if not candidates:
        return {
            "date": for_date.isoformat(),
            "recommended_exercise": None,
            "recommended_video": None,
            "recommendation_type": "recovery",
            "reasoning_summary": "No suitable exercises in catalog for your current readiness. Add recovery/low options or try again later.",
            "warnings": "; ".join(readiness.warnings) if readiness.warnings else "",
            "coach_message": "Rest or do light movement today.",
            "error": "no_candidates",
        }

    readiness_summary = (
        f"Score {readiness.score:.2f}, allowed intensity: {readiness.allowed_intensity}. "
        f"Warnings: {'; '.join(readiness.warnings) or 'None'}."
    )
    context = build_recommendation_context(
        user=user,
        for_date=for_date,
        today_checkin=check_in,
        recent_workout_logs=recent_logs,
        recent_recommendations=recent_recs,
        candidate_exercises=candidates,
        readiness_summary=readiness_summary,
    )
    candidate_payloads = context["candidate_exercises"]

    llm_result = recommend_workout_from_candidates(
        context=context,
        candidates=candidate_payloads,
    )

    recommended_id = llm_result.get("recommended_exercise_id")
    recommended_exercise = None
    if recommended_id:
        recommended_exercise = Exercise.objects.filter(pk=recommended_id).first()
        if not recommended_exercise and candidates:
            recommended_exercise = candidates[0]

    with transaction.atomic():
        rec, _ = TrainingRecommendation.objects.update_or_create(
            user=user,
            date=for_date,
            defaults={
                "recommended_exercise": recommended_exercise,
                "recommendation_type": llm_result.get("recommendation_type") or "moderate",
                "reasoning_summary": llm_result.get("reasoning_summary") or "",
                "warnings": llm_result.get("warnings") or "",
                "coach_message": llm_result.get("coach_message") or "",
                "rule_based_payload": readiness.payload,
                "llm_payload": llm_result,
            },
        )

    exercise_data = None
    if rec.recommended_exercise:
        exercise_data = _exercise_to_response(rec.recommended_exercise)

    return {
        "date": rec.date.isoformat(),
        "recommended_exercise": exercise_data,
        "recommended_video": None,
        "recommendation_type": rec.recommendation_type,
        "reasoning_summary": rec.reasoning_summary,
        "warnings": rec.warnings,
        "coach_message": rec.coach_message,
    }
