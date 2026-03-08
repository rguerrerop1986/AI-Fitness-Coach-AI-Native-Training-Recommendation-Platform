"""
Orchestrates daily recommendation: check-in -> history -> readiness -> candidates -> OpenAI -> persist.
"""
from datetime import date, timedelta
from typing import Any, Dict, Optional

from django.db import transaction

from apps.training.models import DailyCheckIn, TrainingRecommendation, TrainingVideo
from apps.training.selectors import get_checkin_for_date, get_recent_workout_logs
from apps.training.services.readiness import evaluate_readiness
from apps.training.services.video_selector import get_candidate_videos
from apps.training.services.openai_coach import recommend_workout_from_candidates


def _summarize_check_in(check_in: Optional[DailyCheckIn]) -> str:
    """Build a short text summary of the check-in for the LLM."""
    if not check_in:
        return "No check-in for this date."
    parts = []
    if check_in.hours_sleep is not None:
        parts.append(f"Sleep: {check_in.hours_sleep}h, quality {check_in.sleep_quality or 'N/A'}")
    if check_in.energy_level is not None:
        parts.append(f"Energy: {check_in.energy_level}/10")
    if check_in.motivation_level is not None:
        parts.append(f"Motivation: {check_in.motivation_level}/10")
    if check_in.soreness_legs is not None:
        parts.append(f"Soreness legs: {check_in.soreness_legs}/10")
    if check_in.soreness_arms is not None:
        parts.append(f"Soreness arms: {check_in.soreness_arms}/10")
    if check_in.joint_pain:
        parts.append("Joint pain: yes")
    if check_in.notes:
        parts.append(f"Notes: {check_in.notes[:200]}")
    return " | ".join(parts) if parts else "No details."


def _summarize_recent_logs(logs: list) -> str:
    """Build a short summary of recent workout logs."""
    if not logs:
        return "No recent workouts."
    lines = []
    for log in logs[:7]:
        name = log.video.name if log.video else "Unknown"
        rpe = log.rpe if log.rpe is not None else "N/A"
        pain = "pain" if log.pain_during_workout else "no pain"
        lines.append(f"- {log.date}: {name}, RPE {rpe}, {pain}")
    return "\n".join(lines)


def generate_recommendation(user, for_date: date) -> Dict[str, Any]:
    """
    Generate (or reuse) a training recommendation for the user on the given date.
    - Loads check-in and recent workout logs.
    - Evaluates readiness (deterministic).
    - Selects 3-5 candidate videos.
    - Calls OpenAI to pick one and get reasoning/message.
    - Saves or updates TrainingRecommendation.
    Returns a dict suitable for API response (date, recommended_video, recommendation_type, etc.).
    """
    check_in = get_checkin_for_date(user, for_date)
    recent_logs = list(get_recent_workout_logs(user, days=14, before_date=for_date))

    readiness = evaluate_readiness(check_in, recent_logs, for_date)
    candidates = get_candidate_videos(readiness, check_in, limit=5)

    if not candidates:
        # No safe candidates: return a structured error response (caller may 400/404)
        return {
            "date": for_date.isoformat(),
            "recommended_video": None,
            "recommendation_type": "recovery",
            "reasoning_summary": "No suitable videos in catalog for your current readiness. Add recovery/low options or try again later.",
            "warnings": "; ".join(readiness.warnings) if readiness.warnings else "",
            "coach_message": "Rest or do light movement today.",
            "error": "no_candidates",
        }

    check_in_summary = _summarize_check_in(check_in)
    recent_history_summary = _summarize_recent_logs(recent_logs)
    readiness_summary = f"Score {readiness.score:.2f}, allowed intensity: {readiness.allowed_intensity}. Warnings: {'; '.join(readiness.warnings) or 'None'}."

    llm_result = recommend_workout_from_candidates(
        check_in_summary=check_in_summary,
        recent_history_summary=recent_history_summary,
        readiness_summary=readiness_summary,
        candidates=candidates,
    )

    recommended_id = llm_result.get("recommended_workout_id")
    recommended_video = None
    if recommended_id:
        recommended_video = TrainingVideo.objects.filter(pk=recommended_id).first()

    with transaction.atomic():
        rec, _ = TrainingRecommendation.objects.update_or_create(
            user=user,
            date=for_date,
            defaults={
                "recommended_video": recommended_video,
                "recommendation_type": llm_result.get("recommendation_type") or "moderate",
                "reasoning_summary": llm_result.get("reasoning_summary") or "",
                "warnings": llm_result.get("warnings") or "",
                "coach_message": llm_result.get("coach_message") or "",
                "rule_based_payload": readiness.payload,
                "llm_payload": llm_result,
            },
        )

    # Build API-friendly response
    video_data = None
    if rec.recommended_video:
        v = rec.recommended_video
        video_data = {
            "id": v.id,
            "name": v.name,
            "category": v.category,
            "difficulty": v.difficulty,
            "duration_minutes": v.duration_minutes,
        }

    return {
        "date": rec.date.isoformat(),
        "recommended_video": video_data,
        "recommendation_type": rec.recommendation_type,
        "reasoning_summary": rec.reasoning_summary,
        "warnings": rec.warnings,
        "coach_message": rec.coach_message,
    }
