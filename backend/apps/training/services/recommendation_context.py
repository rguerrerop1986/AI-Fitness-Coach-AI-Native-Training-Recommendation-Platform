"""
Build structured recommendation context for the LLM: user, check-in, history, feedbacks, previous recommendations, candidates.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation, WorkoutLog


def _serialize_checkin(check_in: Optional[DailyCheckIn]) -> Optional[Dict[str, Any]]:
    if not check_in:
        return None
    return {
        "date": check_in.date.isoformat(),
        "hours_sleep": float(check_in.hours_sleep) if check_in.hours_sleep is not None else None,
        "sleep_quality": check_in.sleep_quality,
        "energy_level": check_in.energy_level,
        "motivation_level": check_in.motivation_level,
        "mood": check_in.mood or "",
        "soreness_legs": check_in.soreness_legs,
        "soreness_arms": check_in.soreness_arms,
        "soreness_core": check_in.soreness_core,
        "soreness_shoulders": check_in.soreness_shoulders,
        "joint_pain": check_in.joint_pain,
        "pain_notes": check_in.pain_notes or "",
        "did_gym_today": check_in.did_gym_today,
        "did_gym_yesterday": check_in.did_gym_yesterday,
        "gym_focus": check_in.gym_focus or "",
        "wants_intensity": check_in.wants_intensity,
        "notes": (check_in.notes or "")[:500],
    }


def _serialize_workout_log(log: WorkoutLog) -> Dict[str, Any]:
    return {
        "date": log.date.isoformat(),
        "exercise_or_video_name": log.video.name if log.video else "Unknown",
        "completed": log.completed,
        "rpe": log.rpe,
        "satisfaction": log.satisfaction,
        "performance": log.performance or "",
        "pain_during_workout": log.pain_during_workout,
        "recovery_fast": log.recovery_fast,
        "body_feedback": (log.body_feedback or "")[:300],
        "emotional_feedback": (log.emotional_feedback or "")[:300],
    }


def _serialize_recommendation(rec: TrainingRecommendation) -> Dict[str, Any]:
    ex = rec.recommended_exercise
    return {
        "date": rec.date.isoformat(),
        "recommendation_type": rec.recommendation_type,
        "recommended_exercise_id": ex.id if ex else None,
        "recommended_exercise_name": ex.name if ex else (rec.recommended_video.name if rec.recommended_video else None),
        "reasoning_summary": (rec.reasoning_summary or "")[:300],
        "coach_message": (rec.coach_message or "")[:200],
    }


def _serialize_exercise(ex: Exercise) -> Dict[str, Any]:
    return {
        "id": ex.id,
        "name": ex.name,
        "muscle_group": ex.muscle_group,
        "difficulty": ex.difficulty,
        "intensity": ex.intensity,
        "tags": list(ex.tags) if ex.tags else [],
        "instructions": (ex.instructions or "")[:400],
    }


def build_recommendation_context(
    user,
    for_date: date,
    today_checkin: Optional[DailyCheckIn],
    recent_workout_logs: List[WorkoutLog],
    recent_recommendations: List[TrainingRecommendation],
    candidate_exercises: List[Exercise],
    readiness_summary: str = "",
) -> Dict[str, Any]:
    """
    Build a structured JSON payload for the recommendation LLM.
    Includes: user, date, today_checkin, recent_training_logs, recent_feedbacks (from logs),
    previous_recommendations, candidate_exercises.
    """
    recent_feedbacks = [_serialize_workout_log(log) for log in recent_workout_logs]
    return {
        "user": {
            "id": user.id,
            "name": getattr(user, "get_full_name", lambda: getattr(user, "username", ""))() or str(user),
        },
        "date": for_date.isoformat(),
        "today_checkin": _serialize_checkin(today_checkin),
        "recent_training_logs": recent_feedbacks,
        "recent_feedbacks": recent_feedbacks,
        "previous_recommendations": [_serialize_recommendation(r) for r in recent_recommendations],
        "candidate_exercises": [_serialize_exercise(e) for e in candidate_exercises],
        "readiness_summary": readiness_summary,
    }
