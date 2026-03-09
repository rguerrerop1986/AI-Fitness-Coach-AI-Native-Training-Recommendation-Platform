"""
Orchestrates daily recommendation via LangGraph: context -> readiness -> route -> candidates
-> LLM build -> validate -> (persist | fallback -> persist).
Uses real Exercise catalog and persisted TrainingRecommendation / TrainingRecommendationExercise.
"""
from datetime import date
from typing import Any

from apps.training.graph.recommendation_graph import graph


class TrainingRecommendationService:
    """Production recommendation engine driven by LangGraph."""

    def generate(self, user_id: int, for_date: str) -> dict[str, Any]:
        """
        Run the recommendation graph and return the recommendation plan plus metadata.
        for_date: ISO date string (YYYY-MM-DD).
        Returns dict with recommendation_plan, persisted_recommendation_id, date, and optional error.
        """
        initial_state: dict[str, Any] = {
            "user_id": user_id,
            "date": for_date,
        }
        try:
            result = graph.invoke(initial_state)
        except Exception as e:
            return {
                "date": for_date,
                "recommendation_plan": {
                    "recommendation_type": "recovery",
                    "reasoning_summary": "Recommendation engine failed.",
                    "coach_message": "Take a rest day and try again later.",
                    "exercises": [],
                },
                "persisted_recommendation_id": None,
                "error": str(e),
            }

        recommendation_plan = result.get("recommendation_plan")
        if not recommendation_plan or not isinstance(recommendation_plan, dict):
            return {
                "date": for_date,
                "recommendation_plan": {
                    "recommendation_type": "recovery",
                    "reasoning_summary": "",
                    "coach_message": "Recommendation structure missing.",
                    "exercises": [],
                },
                "persisted_recommendation_id": result.get("persisted_recommendation_id"),
                "readiness_score": result.get("readiness_score"),
                "warnings": result.get("warnings") or [],
                "error": "missing_plan",
            }
        # Empty exercises is valid for recovery, mobility, rest_day
        persisted_id = result.get("persisted_recommendation_id")
        error = result.get("error")
        if not error and recommendation_plan and persisted_id is None:
            error = "persistence_failed"
        return {
            "date": for_date,
            "recommendation_plan": recommendation_plan,
            "persisted_recommendation_id": persisted_id,
            "readiness_score": result.get("readiness_score"),
            "warnings": result.get("warnings") or [],
            "error": error,
        }


# Backward-compatible function for existing callers (e.g. view can use either)
def generate_recommendation(user, for_date: date) -> dict[str, Any]:
    """
    Generate (or reuse) a training recommendation for the user on the given date.
    Uses TrainingRecommendationService and returns a response shape compatible with
    the existing API (date, recommended_exercise, recommendation_type, etc.) plus recommendation_plan.
    """
    from apps.catalogs.models import Exercise

    service = TrainingRecommendationService()
    out = service.generate(user.id, for_date.isoformat())
    plan = out.get("recommendation_plan") or {}
    exercises_plan = plan.get("exercises") or []

    # First recommended exercise for backward compat
    first_ex_id = exercises_plan[0].get("exercise_id") if exercises_plan else None
    recommended_exercise = None
    if first_ex_id:
        recommended_exercise = Exercise.objects.filter(pk=first_ex_id).first()
    if recommended_exercise:
        exercise_data = {
            "id": recommended_exercise.id,
            "name": recommended_exercise.name,
            "muscle_group": recommended_exercise.muscle_group,
            "difficulty": recommended_exercise.difficulty,
            "intensity": recommended_exercise.intensity,
            "tags": list(recommended_exercise.tags) if recommended_exercise.tags else [],
        }
    else:
        exercise_data = None

    return {
        "date": out["date"],
        "recommended_exercise": exercise_data,
        "recommended_video": None,
        "recommendation_type": plan.get("recommendation_type") or "moderate",
        "reasoning_summary": plan.get("reasoning_summary") or "",
        "warnings": "\n".join(out.get("warnings") or []),
        "coach_message": plan.get("coach_message") or "",
        "recommendation_plan": plan,
        "persisted_recommendation_id": out.get("persisted_recommendation_id"),
        "readiness_score": out.get("readiness_score"),
        "error": out.get("error"),
    }
