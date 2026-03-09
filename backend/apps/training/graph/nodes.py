"""
LangGraph node implementations for the recommendation workflow.
All nodes read/write RecommendationState; data comes from Django ORM (no mocks).
"""
import logging
from datetime import date
from typing import Any

from django.db.models import QuerySet

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation, WorkoutLog
from apps.training.selectors import (
    get_checkin_for_date,
    get_recent_recommendations,
    get_recent_workout_logs,
)
from apps.training.graph.state import RecommendationState

logger = logging.getLogger(__name__)


def _serialize_checkin(check_in: DailyCheckIn | None) -> dict | None:
    if not check_in:
        return None
    return {
        "date": check_in.date.isoformat(),
        "hours_sleep": float(check_in.hours_sleep) if check_in.hours_sleep is not None else None,
        "sleep_quality": check_in.sleep_quality,
        "energy_level": check_in.energy_level,
        "motivation_level": check_in.motivation_level,
        "soreness_legs": check_in.soreness_legs,
        "soreness_arms": check_in.soreness_arms,
        "soreness_core": check_in.soreness_core,
        "soreness_shoulders": check_in.soreness_shoulders,
        "joint_pain": check_in.joint_pain,
        "pain_notes": check_in.pain_notes or "",
        "wants_intensity": check_in.wants_intensity,
    }


def _serialize_workout(log: WorkoutLog) -> dict:
    return {
        "date": log.date.isoformat(),
        "video_name": log.video.name if log.video else None,
        "completed": log.completed,
        "rpe": log.rpe,
        "satisfaction": log.satisfaction,
        "pain_during_workout": log.pain_during_workout,
        "felt_drained": log.felt_drained,
    }


def _serialize_recommendation(rec: TrainingRecommendation) -> dict:
    ex = rec.recommended_exercise
    return {
        "date": rec.date.isoformat(),
        "recommendation_type": rec.recommendation_type,
        "recommended_exercise_id": ex.id if ex else None,
        "recommended_exercise_name": ex.name if ex else None,
    }


def _serialize_exercise(ex: Exercise) -> dict:
    return {
        "id": ex.id,
        "name": ex.name,
        "muscle_group": ex.muscle_group,
        "difficulty": ex.difficulty,
        "intensity": ex.intensity,
        "tags": list(ex.tags) if ex.tags else [],
        "equipment_type": ex.equipment_type or "",
    }


def load_user_context(state: RecommendationState) -> RecommendationState:
    """
    Load today's check-in, recent workout logs, previous recommendations, and exercise catalog from DB.
    Never hardcode exercises; always query Exercise table.
    """
    user_id = state["user_id"]
    date_str = state["date"]
    for_date = date.fromisoformat(date_str)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {**state, "error": "User not found"}

    check_in = get_checkin_for_date(user, for_date)
    recent_logs_qs: QuerySet[WorkoutLog] = get_recent_workout_logs(user, days=14, before_date=for_date)
    recent_recs_qs = get_recent_recommendations(user, days=14, before_date=for_date)

    recent_workouts = [_serialize_workout(log) for log in list(recent_logs_qs)]
    previous_recommendations = [_serialize_recommendation(r) for r in list(recent_recs_qs)]

    # Full exercise catalog (active only) for filtering in later nodes
    catalog = list(
        Exercise.objects.filter(is_active=True).values(
            "id", "name", "muscle_group", "difficulty", "intensity", "tags", "equipment_type"
        )
    )
    exercise_catalog = [
        {**row, "tags": list(row["tags"]) if row.get("tags") else []}
        for row in catalog
    ]

    return {
        **state,
        "checkin": _serialize_checkin(check_in),
        "recent_workouts": recent_workouts,
        "previous_recommendations": previous_recommendations,
        "exercise_catalog": exercise_catalog,
        "error": None,
    }


def analyze_readiness(state: RecommendationState) -> RecommendationState:
    """
    Compute readiness_score (0–1) and readiness_flags from check-in and recent workouts.
    Deterministic: sleep > 7 → +0.2, energy > 7 → +0.2, pain > 5 → -0.4.
    """
    score = 0.5  # baseline
    flags: list[str] = []

    checkin = state.get("checkin")
    recent = state.get("recent_workouts") or []

    if checkin:
        hours_sleep = checkin.get("hours_sleep")
        if hours_sleep is not None:
            if float(hours_sleep) > 7:
                score += 0.2
            elif float(hours_sleep) < 5:
                score -= 0.2
                flags.append("low_sleep")

        energy = checkin.get("energy_level")
        if energy is not None:
            if energy > 7:
                score += 0.2
            elif energy <= 3:
                score -= 0.3
                flags.append("low_energy")

        # Pain: use highest soreness or joint_pain
        pain_level = max(
            checkin.get("soreness_legs") or 0,
            checkin.get("soreness_arms") or 0,
            checkin.get("soreness_core") or 0,
            checkin.get("soreness_shoulders") or 0,
        )
        if checkin.get("joint_pain"):
            pain_level = max(pain_level, 7)
        if pain_level > 5:
            score -= 0.4
            flags.append("pain_or_soreness")

    # Recent workout pain
    for w in recent[:3]:
        if w.get("pain_during_workout") or w.get("felt_drained"):
            score -= 0.1
            if "recent_fatigue_or_pain" not in flags:
                flags.append("recent_fatigue_or_pain")
            break

    readiness_score = max(0.0, min(1.0, score))
    return {
        **state,
        "readiness_score": readiness_score,
        "readiness_flags": flags,
    }


def route_recommendation_type(state: RecommendationState) -> RecommendationState:
    """
    Set recommendation_type: recovery, mobility, upper_strength, lower_strength,
    cardio, full_body, or rest_day based on readiness_score, pain flags, and recent workouts.
    """
    score = state.get("readiness_score", 0.5)
    flags = state.get("readiness_flags") or []
    recent = state.get("recent_workouts") or []
    prev = state.get("previous_recommendations") or []

    # Repeated muscle groups in last 2 recommendations -> vary
    recent_muscle_groups: set[str] = set()
    for r in prev[:2]:
        # We don't have muscle_group in serialized rec; use type as proxy
        rt = r.get("recommendation_type") or ""
        if "upper" in rt or "strength" in rt:
            recent_muscle_groups.add("upper")
        if "lower" in rt:
            recent_muscle_groups.add("lower")
        if "cardio" in rt:
            recent_muscle_groups.add("cardio")

    if score <= 0.3 or "pain_or_soreness" in flags:
        rec_type = "recovery"
    elif score <= 0.45:
        rec_type = "mobility"
    elif "low_energy" in flags or "low_sleep" in flags:
        rec_type = "recovery" if score < 0.5 else "mobility"
    elif score >= 0.85 and "cardio" not in recent_muscle_groups:
        rec_type = "cardio"
    elif score >= 0.7:
        if "upper" in recent_muscle_groups and "lower" not in recent_muscle_groups:
            rec_type = "lower_strength"
        elif "lower" in recent_muscle_groups and "upper" not in recent_muscle_groups:
            rec_type = "upper_strength"
        else:
            rec_type = "full_body"
    elif score >= 0.5:
        rec_type = "upper_strength" if "upper" not in recent_muscle_groups else "lower_strength"
    else:
        rec_type = "mobility"

    return {**state, "recommendation_type": rec_type}


def retrieve_candidate_exercises(state: RecommendationState) -> RecommendationState:
    """
    Query Exercise table; filter by recommendation_type, intensity (from readiness),
    injury/pain flags, and recent repetition (avoid same muscle group overload).
    """
    from apps.training.services.exercise_selector import get_candidate_exercises
    from apps.training.services.readiness import ReadinessResult, evaluate_readiness

    user_id = state["user_id"]
    date_str = state["date"]
    for_date = date.fromisoformat(date_str)
    rec_type = state.get("recommendation_type") or "moderate"
    catalog = state.get("exercise_catalog") or []

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {**state, "candidate_exercises": [], "error": "User not found"}

    check_in = get_checkin_for_date(user, for_date)
    recent_logs = list(get_recent_workout_logs(user, days=14, before_date=for_date))
    readiness = evaluate_readiness(check_in, recent_logs, for_date)

    # Map graph recommendation_type to allowed intensity for existing selector
    type_to_intensity = {
        "rest_day": "recovery",
        "recovery": "recovery",
        "mobility": "recovery",
        "upper_strength": "intense",
        "lower_strength": "intense",
        "cardio": "moderate",
        "full_body": "moderate",
    }
    allowed = type_to_intensity.get(rec_type, "moderate")
    readiness = ReadinessResult(
        score=readiness.score,
        warnings=readiness.warnings,
        allowed_intensity=allowed,
        payload=readiness.payload,
    )

    candidates = get_candidate_exercises(readiness, check_in, limit=10)

    # Filter by recommendation_type / muscle focus
    muscle_filter = {
        "upper_strength": {"chest", "back", "shoulders", "biceps", "triceps", "forearms"},
        "lower_strength": {"quads", "hamstrings", "glutes", "calves"},
        "cardio": {"cardio", "full_body"},
        "core_only": {"core"},
    }
    if rec_type in muscle_filter:
        allowed_groups = muscle_filter[rec_type]
        candidates = [c for c in candidates if c.muscle_group in allowed_groups]
    elif rec_type in ("recovery", "mobility"):
        candidates = [c for c in candidates if c.intensity <= 4]
    elif rec_type == "rest_day":
        candidates = [c for c in candidates if c.intensity <= 2][:3]

    if not candidates and rec_type != "rest_day":
        # Fallback: any low-intensity
        candidates = list(Exercise.objects.filter(is_active=True, intensity__lte=5).order_by("intensity")[:8])

    candidate_payloads = [_serialize_exercise(c) for c in candidates]
    return {
        **state,
        "candidate_exercises": candidate_payloads,
    }


def build_recommendation(state: RecommendationState) -> RecommendationState:
    """
    Use LangChain with structured output: select only from candidate_exercises,
    generate sets/reps/rest, reasoning_summary, coach_message. Return recommendation_plan dict.
    """
    from apps.training.prompts.recommendation_prompt import build_recommendation_plan_with_llm

    plan = build_recommendation_plan_with_llm(state)
    return {
        **state,
        "recommendation_plan": plan,
    }


def validate_recommendation(state: RecommendationState) -> RecommendationState:
    """
    Validate: exercise IDs exist, belong to candidate list, no injury conflicts, reasonable volume.
    Populate validation_errors and warnings.
    """
    errors: list[str] = []
    warnings_list: list[str] = state.get("warnings") or []

    plan = state.get("recommendation_plan") or {}
    candidates = state.get("candidate_exercises") or []
    candidate_ids = {c["id"] for c in candidates}
    checkin = state.get("checkin") or {}

    exercises_plan = plan.get("exercises") or []
    if not exercises_plan and state.get("recommendation_type") != "rest_day":
        errors.append("recommendation_plan has no exercises")

    total_sets = 0
    for i, item in enumerate(exercises_plan):
        eid = item.get("exercise_id")
        if eid is None:
            errors.append(f"exercise at position {i} missing exercise_id")
            continue
        if eid not in candidate_ids:
            errors.append(f"exercise_id {eid} not in candidate list")
        sets_val = item.get("sets") or 0
        reps_val = item.get("reps") or 0
        if sets_val < 0 or sets_val > 20:
            errors.append(f"exercise {eid}: sets must be 0-20")
        if reps_val < 0 or reps_val > 50:
            errors.append(f"exercise {eid}: reps must be 0-50")
        total_sets += sets_val

    if total_sets > 30:
        warnings_list.append("high_volume")

    if checkin.get("joint_pain") and plan.get("recommendation_type") not in ("recovery", "mobility", "rest_day"):
        warnings_list.append("pain_recommend_lighter")

    return {
        **state,
        "validation_errors": errors,
        "warnings": warnings_list,
    }


def fallback_recommendation(state: RecommendationState) -> RecommendationState:
    """
    On validation failure or empty candidates: produce a safe recovery recommendation.
    Never crash the API.
    """
    candidates = state.get("candidate_exercises") or []
    catalog = state.get("exercise_catalog") or []

    # Prefer first low-intensity candidate; else first from catalog
    low = [c for c in candidates if c.get("intensity", 10) <= 4]
    fallback_exercises = low[:3] if low else catalog[:3]

    exercises_plan = []
    for i, ex in enumerate(fallback_exercises):
        exercises_plan.append({
            "exercise_id": ex.get("id"),
            "sets": 2,
            "reps": 10,
            "rest_seconds": 60,
            "notes": "Recovery option.",
            "position": i,
        })

    plan = {
        "recommendation_type": "recovery",
        "reasoning_summary": "Safe recovery recommendation (fallback).",
        "coach_message": "Take it easy today. Listen to your body.",
        "exercises": exercises_plan,
    }
    return {
        **state,
        "recommendation_plan": plan,
        "validation_errors": [],
        "warnings": (state.get("warnings") or []) + ["fallback_used"],
    }


def persist_recommendation(state: RecommendationState) -> RecommendationState:
    """
    Save TrainingRecommendation and TrainingRecommendationExercise rows.
    Return persisted_recommendation_id.
    """
    from django.db import transaction
    from apps.training.models import TrainingRecommendationExercise

    user_id = state["user_id"]
    date_str = state["date"]
    for_date = date.fromisoformat(date_str)
    plan = state.get("recommendation_plan") or {}

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {**state, "persisted_recommendation_id": None}

    with transaction.atomic():
        rec = TrainingRecommendation.objects.update_or_create(
            user=user,
            date=for_date,
            defaults={
                "recommendation_type": plan.get("recommendation_type") or "moderate",
                "reasoning_summary": plan.get("reasoning_summary") or "",
                "coach_message": plan.get("coach_message") or "",
                "warnings": "\n".join(state.get("warnings") or []),
                "readiness_score": state.get("readiness_score"),
                "metadata": plan.get("metadata") or {},
                "rule_based_payload": {"readiness_flags": state.get("readiness_flags") or []},
                "llm_payload": plan,
            },
        )[0]

        # Link first recommended exercise for backward compat
        exercises_plan = plan.get("exercises") or []
        first_ex_id = exercises_plan[0].get("exercise_id") if exercises_plan else None
        if first_ex_id:
            rec.recommended_exercise_id = first_ex_id
            rec.save(update_fields=["recommended_exercise_id"])

        TrainingRecommendationExercise.objects.filter(recommendation=rec).delete()
        for i, item in enumerate(exercises_plan):
            ex_id = item.get("exercise_id")
            if ex_id is None:
                continue
            TrainingRecommendationExercise.objects.create(
                recommendation=rec,
                exercise_id=ex_id,
                sets=item.get("sets") or 0,
                reps=item.get("reps") or 0,
                rest_seconds=item.get("rest_seconds") or 0,
                notes=item.get("notes") or "",
                position=i,
            )

    return {
        **state,
        "persisted_recommendation_id": rec.id,
    }
