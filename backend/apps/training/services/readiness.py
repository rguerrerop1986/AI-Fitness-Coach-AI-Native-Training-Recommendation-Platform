"""
Deterministic readiness evaluation: score, warnings, and allowed intensity.
Used before video selection so the LLM only chooses from safe candidates.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from apps.training.models import DailyCheckIn, WorkoutLog
from apps.training.selectors import get_recent_workout_logs


@dataclass
class ReadinessResult:
    """Result of evaluating user readiness for training."""

    score: float  # 0.0 - 1.0
    warnings: List[str]
    allowed_intensity: str  # 'recovery' | 'light' | 'moderate' | 'intense' | 'max'
    payload: dict  # raw signals for debugging / LLM context


def evaluate_readiness(
    check_in: Optional[DailyCheckIn],
    recent_logs: List[WorkoutLog],
    for_date: date,
) -> ReadinessResult:
    """
    Evaluate readiness from check-in and recent workout history.
    Returns score (0-1), list of warnings, and allowed_intensity level.
    """
    warnings: List[str] = []
    score = 1.0
    # Allowed intensity: recovery < light < moderate < intense < max
    allowed = "max"

    # --- Check-in signals ---
    if check_in:
        # Joint pain -> force recovery only
        if check_in.joint_pain:
            score = min(score, 0.3)
            allowed = "recovery"
            warnings.append("Joint pain reported; limit to recovery only.")

        # Poor sleep
        if check_in.hours_sleep is not None and float(check_in.hours_sleep) < 5:
            score = min(score, 0.6)
            if allowed == "max":
                allowed = "moderate"
            warnings.append("Low sleep hours; consider moderate or lighter session.")
        if check_in.sleep_quality is not None and check_in.sleep_quality <= 3:
            score = min(score, 0.7)
            if allowed not in ("recovery", "light") and allowed == "max":
                allowed = "intense"

        # Low energy
        if check_in.energy_level is not None and check_in.energy_level <= 3:
            score = min(score, 0.5)
            if allowed not in ("recovery", "light"):
                allowed = "light"
            warnings.append("Low energy level; recommend light or recovery.")

        # High soreness (legs) -> avoid explosive / heavy leg stress
        legs = check_in.soreness_legs or 0
        if legs >= 7:
            score = min(score, 0.5)
            if allowed == "max":
                allowed = "moderate"
            warnings.append("High leg soreness; avoid explosive or heavy leg work.")
        elif legs >= 5:
            if allowed == "max":
                allowed = "intense"

        # General soreness (any zone high)
        max_sore = max(
            check_in.soreness_arms or 0,
            check_in.soreness_core or 0,
            check_in.soreness_shoulders or 0,
        )
        if max_sore >= 7:
            score = min(score, 0.6)
            if allowed not in ("recovery", "light"):
                allowed = "moderate"

    # --- Recent workout load ---
    if recent_logs:
        # High RPE in last 1-2 sessions -> reduce intensity
        recent_two = recent_logs[:2]
        high_rpe_count = sum(1 for log in recent_two if (log.rpe or 0) >= 8)
        if high_rpe_count >= 1 and len(recent_two) >= 1:
            score = min(score, 0.75)
            if allowed == "max":
                allowed = "intense"
        if high_rpe_count >= 2:
            score = min(score, 0.6)
            if allowed not in ("recovery", "light"):
                allowed = "moderate"
            warnings.append("Recent high RPE sessions; allow recovery.")

        # Consecutive intense days (e.g. 2+ days with RPE >= 7)
        last_7 = recent_logs[:7]
        intense_days = sum(1 for log in last_7 if (log.rpe or 0) >= 7)
        if intense_days >= 3:
            score = min(score, 0.65)
            if allowed not in ("recovery", "light"):
                allowed = "moderate"
            warnings.append("Several intense days recently; consider moderate or recovery.")

        # Pain during recent workout
        last_log = recent_logs[0] if recent_logs else None
        if last_log and last_log.pain_during_workout:
            score = min(score, 0.4)
            allowed = "recovery"
            warnings.append("Pain during last workout; recommend recovery only.")

    # --- Gym context (optional: did gym today/yesterday -> might want lighter cardio) ---
    if check_in:
        if check_in.did_gym_today or check_in.did_gym_yesterday:
            if allowed == "max":
                allowed = "intense"
            # Don't add warning every time; only if combined with other factors
            if score < 0.8:
                warnings.append("Gym done recently; today's session can be moderate.")

    # Clamp score
    score = max(0.0, min(1.0, score))
    payload = {
        "score": score,
        "allowed_intensity": allowed,
        "warnings": warnings,
        "has_check_in": check_in is not None,
        "recent_logs_count": len(recent_logs),
    }
    return ReadinessResult(
        score=score,
        warnings=warnings,
        allowed_intensity=allowed,
        payload=payload,
    )
