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
                "session_goal": "",
                "recommendation_plan": {
                    "session_goal": "",
                    "recommendation_type": "recovery",
                    "reasoning_summary": "Recommendation engine failed.",
                    "coach_message": "Take a rest day and try again later.",
                    "estimated_duration_minutes": 0,
                    "intensity": "low",
                    "warnings": "",
                    "exercises": [],
                },
                "recommended_exercises": [],
                "estimated_duration_minutes": 0,
                "intensity": "low",
                "persisted_recommendation_id": None,
                "error": str(e),
            }

        recommendation_plan = result.get("recommendation_plan")
        if not recommendation_plan or not isinstance(recommendation_plan, dict):
            return {
                "date": for_date,
                "session_goal": "",
                "recommendation_plan": {
                    "session_goal": "",
                    "recommendation_type": "recovery",
                    "reasoning_summary": "",
                    "coach_message": "Recommendation structure missing.",
                    "estimated_duration_minutes": 0,
                    "intensity": "low",
                    "warnings": "",
                    "exercises": [],
                },
                "recommended_exercises": [],
                "estimated_duration_minutes": 0,
                "intensity": "low",
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
        exercises = recommendation_plan.get("exercises") or []
        return {
            "date": for_date,
            "session_goal": recommendation_plan.get("session_goal") or "",
            "recommendation_plan": recommendation_plan,
            "recommended_exercises": exercises,
            "estimated_duration_minutes": recommendation_plan.get("estimated_duration_minutes"),
            "intensity": recommendation_plan.get("intensity") or "",
            "persisted_recommendation_id": persisted_id,
            "readiness_score": result.get("readiness_score"),
            "warnings": result.get("warnings") or [],
            "error": error,
        }


# Backward-compatible function for existing callers (e.g. view can use either)
def generate_recommendation(user, for_date: date) -> dict[str, Any]:
    """
    Generate a full daily session recommendation. Returns session_goal, recommended_exercises
    (with names), estimated_duration_minutes, intensity, and recommendation_plan.
    """
    from apps.catalogs.models import Exercise

    service = TrainingRecommendationService()
    out = service.generate(user.id, for_date.isoformat())
    plan = out.get("recommendation_plan") or {}
    exercises_plan = plan.get("exercises") or []

    # Resolve names for recommended_exercises from DB when missing in plan
    exercise_ids = [e.get("exercise_id") for e in exercises_plan if e.get("exercise_id")]
    exercises_by_id = {}
    if exercise_ids:
        for ex in Exercise.objects.filter(pk__in=exercise_ids).only("id", "name"):
            exercises_by_id[ex.id] = ex
    recommended_exercises = []
    for e in exercises_plan:
        ex_id = e.get("exercise_id")
        ex_obj = exercises_by_id.get(ex_id)
        name = e.get("name") or (ex_obj.name if ex_obj else "")
        recommended_exercises.append({
            "exercise_id": ex_id,
            "name": name,
            "sets": e.get("sets") or 0,
            "reps": e.get("reps"),
            "duration_seconds": e.get("duration_seconds"),
            "rest_seconds": e.get("rest_seconds") or 0,
            "notes": e.get("notes") or "",
            "position": e.get("position", 0),
        })

    first_ex_id = exercises_plan[0].get("exercise_id") if exercises_plan else None
    recommended_exercise = Exercise.objects.filter(pk=first_ex_id).first() if first_ex_id else None
    exercise_data = None
    if recommended_exercise:
        exercise_data = {
            "id": recommended_exercise.id,
            "name": recommended_exercise.name,
            "muscle_group": recommended_exercise.muscle_group,
            "difficulty": recommended_exercise.difficulty,
            "intensity": recommended_exercise.intensity,
            "tags": list(recommended_exercise.tags) if recommended_exercise.tags else [],
        }

    return {
        "date": out["date"],
        "session_goal": out.get("session_goal") or plan.get("session_goal") or "",
        "recommendation_plan": plan,
        "recommended_exercises": recommended_exercises,
        "estimated_duration_minutes": out.get("estimated_duration_minutes") or plan.get("estimated_duration_minutes"),
        "intensity": out.get("intensity") or plan.get("intensity") or "",
        "recommended_exercise": exercise_data,
        "recommended_video": None,
        "recommendation_type": plan.get("recommendation_type") or "moderate",
        "reasoning_summary": plan.get("reasoning_summary") or "",
        "warnings": "\n".join(out.get("warnings") or []) if isinstance(out.get("warnings"), list) else (out.get("warnings") or ""),
        "coach_message": plan.get("coach_message") or "",
        "persisted_recommendation_id": out.get("persisted_recommendation_id"),
        "readiness_score": out.get("readiness_score"),
        "error": out.get("error"),
    }
