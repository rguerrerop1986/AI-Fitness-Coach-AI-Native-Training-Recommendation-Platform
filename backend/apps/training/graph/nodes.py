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
    """Serialize a recommendation; include muscle_group from TrainingRecommendationExercise line items when available."""
    ex = rec.recommended_exercise
    exercise_muscle_groups: list[str] = []
    # Use line items (TrainingRecommendationExercise + Exercise) for actual muscle groups when available
    if hasattr(rec, "recommended_exercises"):
        for tre in rec.recommended_exercises.all():
            if getattr(tre, "exercise", None) and getattr(tre.exercise, "muscle_group", None):
                exercise_muscle_groups.append(tre.exercise.muscle_group)
    # Fallback: single recommended_exercise FK (legacy)
    if not exercise_muscle_groups and ex and getattr(ex, "muscle_group", None):
        exercise_muscle_groups.append(ex.muscle_group)
    return {
        "date": rec.date.isoformat(),
        "recommendation_type": rec.recommendation_type,
        "recommended_exercise_id": ex.id if ex else None,
        "recommended_exercise_name": ex.name if ex else None,
        "exercise_muscle_groups": exercise_muscle_groups,
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
    recent_recs_qs = recent_recs_qs.prefetch_related("recommended_exercises__exercise")

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


# Muscle groups that count as "upper" / "lower" / "cardio" for routing
_UPPER_BODY_GROUPS = {"chest", "back", "shoulders", "biceps", "triceps", "forearms"}
_LOWER_BODY_GROUPS = {"quads", "hamstrings", "glutes", "calves"}
_CARDIO_GROUPS = {"cardio", "full_body"}


def _recent_load_from_previous_recommendations(prev: list) -> tuple[set[str], set[str], set[str]]:
    """
    Infer recent muscle-group load from previous recommendations.
    Uses exercise_muscle_groups from TrainingRecommendationExercise + Exercise when available;
    falls back to recommendation_type string heuristics.
    Returns (recent_upper, recent_lower, recent_cardio) as sets of abstract keys for routing.
    """
    recent_upper: set[str] = set()
    recent_lower: set[str] = set()
    recent_cardio: set[str] = set()
    for r in prev[:3]:  # last 3 recommendations
        muscle_groups = r.get("exercise_muscle_groups") or []
        if muscle_groups:
            for mg in muscle_groups:
                mg_lower = (mg or "").lower().strip()
                if mg_lower in _UPPER_BODY_GROUPS:
                    recent_upper.add("upper")
                if mg_lower in _LOWER_BODY_GROUPS:
                    recent_lower.add("lower")
                if mg_lower in _CARDIO_GROUPS:
                    recent_cardio.add("cardio")
        else:
            # Fallback: infer from recommendation_type string
            rt = (r.get("recommendation_type") or "").lower()
            if "upper" in rt or "strength" in rt:
                recent_upper.add("upper")
            if "lower" in rt:
                recent_lower.add("lower")
            if "cardio" in rt:
                recent_cardio.add("cardio")
    return (recent_upper, recent_lower, recent_cardio)


def route_recommendation_type(state: RecommendationState) -> RecommendationState:
    """
    Set recommendation_type: recovery, mobility, upper_strength, lower_strength,
    cardio, full_body, or rest_day based on readiness_score, pain flags, and
    actual historical muscle-group load from TrainingRecommendationExercise + Exercise when available.
    """
    score = state.get("readiness_score", 0.5)
    flags = state.get("readiness_flags") or []
    prev = state.get("previous_recommendations") or []

    recent_upper, recent_lower, recent_cardio = _recent_load_from_previous_recommendations(prev)

    if score <= 0.3 or "pain_or_soreness" in flags:
        rec_type = "recovery"
    elif score <= 0.45:
        rec_type = "mobility"
    elif "low_energy" in flags or "low_sleep" in flags:
        rec_type = "recovery" if score < 0.5 else "mobility"
    elif score >= 0.85 and not recent_cardio:
        rec_type = "cardio"
    elif score >= 0.7:
        if recent_upper and not recent_lower:
            rec_type = "lower_strength"
        elif recent_lower and not recent_upper:
            rec_type = "upper_strength"
        else:
            rec_type = "full_body"
    elif score >= 0.5:
        rec_type = "upper_strength" if not recent_upper else "lower_strength"
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

    candidates = get_candidate_exercises(readiness, check_in, limit=15)

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


# Sane ranges for recommendation validation (DB-backed)
_VALID_SETS_RANGE = (1, 20)
_VALID_REPS_RANGE = (1, 50)
_VALID_REST_SECONDS_RANGE = (0, 600)
_VALID_DURATION_SECONDS_RANGE = (0, 300)

# Types that may have 0 or 1 exercise only (not a full session)
_LOW_LOAD_TYPES = frozenset({"rest_day", "recovery", "mobility_snack", "breathing_reset"})
_MIN_EXERCISES_FULL_SESSION = 3


def validate_recommendation(state: RecommendationState) -> RecommendationState:
    """
    Validate plan: min 3 exercises for full training days; 0-1 only for rest_day/recovery/mobility_snack/breathing_reset.
    Every exercise_id must exist in Exercise, be active, belong to candidate_ids; sane sets/reps/rest_seconds/duration_seconds.
    """
    errors: list[str] = []
    warnings_list: list[str] = state.get("warnings") or []

    plan = state.get("recommendation_plan") or {}
    candidates = state.get("candidate_exercises") or []
    candidate_ids = {c["id"] for c in candidates}
    checkin = state.get("checkin") or {}
    rec_type = (plan.get("recommendation_type") or state.get("recommendation_type") or "").lower()

    exercises_plan = plan.get("exercises") or []

    # Min exercises: full session requires at least 3 unless low-load type
    if rec_type not in _LOW_LOAD_TYPES:
        if len(exercises_plan) < _MIN_EXERCISES_FULL_SESSION:
            errors.append(
                f"recommendation_type '{rec_type}' requires at least {_MIN_EXERCISES_FULL_SESSION} exercises for a full session"
            )
    else:
        if len(exercises_plan) > 2:
            warnings_list.append("low_load_type_with_many_exercises")

    if not exercises_plan and rec_type not in _LOW_LOAD_TYPES:
        errors.append("recommendation_plan has no exercises")

    # DB validation: resolve all exercise_ids in one query (do not rely only on in-memory state)
    plan_eids = [item.get("exercise_id") for item in exercises_plan if item.get("exercise_id") is not None]
    valid_active_ids: set[int] = set()
    if plan_eids:
        valid_active_ids = set(
            Exercise.objects.filter(pk__in=plan_eids, is_active=True).values_list("pk", flat=True)
        )

    seen_eids: set[int] = set()
    total_sets = 0
    sets_min, sets_max = _VALID_SETS_RANGE
    reps_min, reps_max = _VALID_REPS_RANGE
    rest_min, rest_max = _VALID_REST_SECONDS_RANGE

    for i, item in enumerate(exercises_plan):
        eid = item.get("exercise_id")
        if eid is None:
            errors.append(f"exercise at position {i} missing exercise_id")
            continue

        try:
            eid_int = int(eid)
        except (TypeError, ValueError):
            errors.append(f"exercise at position {i}: exercise_id must be an integer")
            continue

        if eid_int not in valid_active_ids:
            errors.append(f"exercise_id {eid_int} does not exist or is not active")
            continue
        if eid_int not in candidate_ids:
            errors.append(f"exercise_id {eid_int} not in candidate list")
            continue
        if eid_int in seen_eids:
            errors.append(f"duplicate exercise_id {eid_int} in plan")
            continue
        seen_eids.add(eid_int)

        sets_val = item.get("sets")
        if sets_val is None:
            errors.append(f"exercise {eid_int}: sets is required")
        else:
            try:
                sets_val = int(sets_val)
                if sets_val < sets_min or sets_val > sets_max:
                    errors.append(f"exercise {eid_int}: sets must be {sets_min}-{sets_max}")
                else:
                    total_sets += sets_val
            except (TypeError, ValueError):
                errors.append(f"exercise {eid_int}: sets must be an integer")

        reps_val = item.get("reps")
        duration_val = item.get("duration_seconds")
        if duration_val is not None:
            try:
                d = int(duration_val)
                d_min, d_max = _VALID_DURATION_SECONDS_RANGE
                if d < d_min or d > d_max:
                    errors.append(f"exercise {eid_int}: duration_seconds must be {d_min}-{d_max}")
            except (TypeError, ValueError):
                errors.append(f"exercise {eid_int}: duration_seconds must be an integer")
        elif reps_val is not None and not isinstance(reps_val, str):
            try:
                r = int(reps_val)
                if r < reps_min or r > reps_max:
                    errors.append(f"exercise {eid_int}: reps must be {reps_min}-{reps_max}")
            except (TypeError, ValueError):
                pass  # allow string reps e.g. "10 por lado"

        rest_val = item.get("rest_seconds")
        if rest_val is not None:
            try:
                rest_val = int(rest_val)
                if rest_val < rest_min or rest_val > rest_max:
                    errors.append(f"exercise {eid_int}: rest_seconds must be {rest_min}-{rest_max}")
            except (TypeError, ValueError):
                errors.append(f"exercise {eid_int}: rest_seconds must be an integer")

    if total_sets > 30:
        warnings_list.append("high_volume")

    if checkin.get("joint_pain") and plan.get("recommendation_type") not in ("recovery", "mobility", "rest_day"):
        warnings_list.append("pain_recommend_lighter")

    return {
        **state,
        "validation_errors": errors,
        "warnings": warnings_list,
    }


# Tags that qualify as safe for fallback (mobility/stretch/recovery/low_impact)
_FALLBACK_SAFE_TAGS = {"mobility", "stretch", "recovery", "low_impact"}
_FALLBACK_MAX_EXERCISES = 5


def _get_safe_fallback_exercises(state: RecommendationState) -> list[dict]:
    """
    Select exercises for fallback by policy only. Never use catalog order.
    1. Prefer exercises tagged mobility/stretch/recovery/low_impact.
    2. Else exercises with intensity <= 3.
    3. Else return empty list (valid rest_day/recovery with zero exercises).
    """
    candidates = state.get("candidate_exercises") or []
    catalog = state.get("exercise_catalog") or []
    pool = candidates if candidates else catalog
    if not pool:
        return []

    def has_safe_tag(ex: dict) -> bool:
        tags = ex.get("tags") or []
        return any(t.lower() in _FALLBACK_SAFE_TAGS for t in tags if isinstance(t, str))

    def intensity(ex: dict) -> int:
        return int(ex.get("intensity") or 10)

    tier1 = [e for e in pool if has_safe_tag(e)]
    tier2 = [e for e in pool if intensity(e) <= 3]

    if tier1:
        chosen = sorted(tier1, key=intensity)[:_FALLBACK_MAX_EXERCISES]
    elif tier2:
        chosen = sorted(tier2, key=intensity)[:_FALLBACK_MAX_EXERCISES]
    else:
        chosen = []

    return chosen


def fallback_recommendation(state: RecommendationState) -> RecommendationState:
    """
    Produce a safe full-session fallback: 2-3 exercises when pool allows; else recovery/mobility_snack with 0-1.
    Includes session_goal, estimated_duration_minutes, intensity.
    """
    fallback_exercises = _get_safe_fallback_exercises(state)
    rec_type = state.get("recommendation_type") or "recovery"

    # If only one or zero safe exercises, classify as low-load (recovery/mobility_snack)
    if len(fallback_exercises) <= 1:
        rec_type = "mobility_snack" if rec_type not in _LOW_LOAD_TYPES else rec_type

    exercises_plan = []
    for i, ex in enumerate(fallback_exercises):
        ex_id = ex.get("id")
        if ex_id is None:
            continue
        exercises_plan.append({
            "exercise_id": ex_id,
            "name": ex.get("name") or "",
            "sets": 2,
            "reps": 10,
            "duration_seconds": None,
            "rest_seconds": 30,
            "notes": "Recovery option.",
            "position": i,
        })

    if len(exercises_plan) >= 2:
        session_goal = "Light full session (fallback)"
        estimated_min = max(15, len(exercises_plan) * 5)
        intensity = "low_to_moderate"
    else:
        session_goal = "Recovery or mobility (fallback)"
        estimated_min = 10 if exercises_plan else 0
        intensity = "low"

    plan = {
        "session_goal": session_goal,
        "recommendation_type": "rest_day" if not exercises_plan else rec_type,
        "reasoning_summary": "Safe recovery recommendation (fallback)."
        if exercises_plan
        else "Rest day or light movement; no exercises selected.",
        "coach_message": "Take it easy today. Listen to your body."
        if exercises_plan
        else "Rest or do light movement. No structured exercises today.",
        "estimated_duration_minutes": estimated_min,
        "intensity": intensity,
        "warnings": "",
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
    Defensive guard: at persistence time, only create line items for exercise_ids that
    still exist and are active; skip invalid/stale ids and record warnings. Do not assume
    prior validation is enough.
    """
    from django.db import transaction
    from apps.training.models import TrainingRecommendationExercise

    user_id = state["user_id"]
    date_str = state["date"]
    for_date = date.fromisoformat(date_str)
    plan = state.get("recommendation_plan") or {}
    exercises_plan = plan.get("exercises") or []

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return {**state, "persisted_recommendation_id": None}

    # Defensive guard: resolve which exercise_ids still exist and are active at persist time
    plan_ex_ids = [item.get("exercise_id") for item in exercises_plan if item.get("exercise_id") is not None]
    valid_active_ids: set[int] = set()
    if plan_ex_ids:
        valid_active_ids = set(
            Exercise.objects.filter(pk__in=plan_ex_ids, is_active=True).values_list("pk", flat=True)
        )
    persistence_warnings: list[str] = []

    with transaction.atomic():
        metadata = dict(plan.get("metadata") or {})
        metadata.setdefault("session_goal", plan.get("session_goal") or "")
        metadata.setdefault("estimated_duration_minutes", plan.get("estimated_duration_minutes"))
        metadata.setdefault("intensity", plan.get("intensity") or "")

        rec = TrainingRecommendation.objects.update_or_create(
            user=user,
            date=for_date,
            defaults={
                "recommendation_type": plan.get("recommendation_type") or "moderate",
                "reasoning_summary": plan.get("reasoning_summary") or "",
                "coach_message": plan.get("coach_message") or "",
                "warnings": "\n".join(state.get("warnings") or []),
                "readiness_score": state.get("readiness_score"),
                "metadata": metadata,
                "rule_based_payload": {"readiness_flags": state.get("readiness_flags") or []},
                "llm_payload": plan,
            },
        )[0]

        # Backward compat: set first recommended exercise only if it is valid at persist time
        first_ex_id = exercises_plan[0].get("exercise_id") if exercises_plan else None
        if first_ex_id and first_ex_id in valid_active_ids:
            rec.recommended_exercise_id = first_ex_id
            rec.save(update_fields=["recommended_exercise_id"])
        elif first_ex_id:
            rec.recommended_exercise_id = None
            rec.save(update_fields=["recommended_exercise_id"])

        TrainingRecommendationExercise.objects.filter(recommendation=rec).delete()
        position = 0
        for item in exercises_plan:
            ex_id = item.get("exercise_id")
            if ex_id is None:
                continue
            if ex_id not in valid_active_ids:
                persistence_warnings.append(f"skipped_invalid_exercise_id:{ex_id}")
                continue
            TrainingRecommendationExercise.objects.create(
                recommendation=rec,
                exercise_id=ex_id,
                sets=item.get("sets") or 0,
                reps=item.get("reps") or 0,
                rest_seconds=item.get("rest_seconds") or 0,
                notes=item.get("notes") or "",
                position=position,
            )
            position += 1

        if persistence_warnings:
            rec.warnings = (rec.warnings or "") + "\n" + "\n".join(persistence_warnings)
            rec.save(update_fields=["warnings"])

    state_warnings = (state.get("warnings") or []) + persistence_warnings
    return {
        **state,
        "persisted_recommendation_id": rec.id,
        "warnings": state_warnings,
    }
