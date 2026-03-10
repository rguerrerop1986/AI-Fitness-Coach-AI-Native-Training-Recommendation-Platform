"""
Prompt and LangChain structured output for full daily session recommendations.
Output is a complete session plan: session_goal, estimated_duration_minutes, intensity,
and recommended_exercises (min 3 for training days unless rest_day/recovery/mobility_snack/breathing_reset).
"""
import json
import logging
from typing import Any, Literal, Union

from pydantic import BaseModel, Field

from apps.training.graph.state import RecommendationState

logger = logging.getLogger(__name__)

# Types that allow 0-1 exercises (low-load / recovery)
LOW_LOAD_RECOMMENDATION_TYPES = frozenset({
    "rest_day",
    "recovery",
    "mobility_snack",
    "breathing_reset",
})

RECOMMENDATION_TYPES = Literal[
    "recovery",
    "mobility",
    "mobility_snack",
    "breathing_reset",
    "upper_strength",
    "lower_strength",
    "cardio",
    "full_body",
    "core_recovery",
    "rest_day",
]

INTENSITY_LEVELS = Literal["low", "low_to_moderate", "moderate", "moderate_to_high", "high"]


class ExerciseItem(BaseModel):
    """One exercise in the session plan. Use duration_seconds for isometric/hold exercises."""

    exercise_id: int = Field(..., description="ID from candidate list")
    sets: int = Field(2, ge=1, le=20, description="Number of sets")
    reps: Union[int, str, None] = Field(None, description="Reps per set (int or e.g. '10 por lado'); omit if using duration_seconds")
    duration_seconds: int | None = Field(None, ge=0, le=300, description="Hold/duration in seconds for isometric (e.g. plank)")
    rest_seconds: int = Field(30, ge=0, le=600, description="Rest between sets (seconds)")
    notes: str = Field("", description="Short coaching note for this exercise")
    position: int = Field(0, ge=0, description="Order in plan")


class RecommendationPlanOutput(BaseModel):
    """Full daily session plan from the LLM."""

    session_goal: str = Field("", description="One-line goal for this session (e.g. Core stability and light conditioning)")
    recommendation_type: RECOMMENDATION_TYPES = Field(
        "recovery",
        description="Session type",
    )
    reasoning_summary: str = Field(
        "",
        description="Why this plan fits today; must reference actual context: sleep, energy, pain, recent workouts, previous recommendations. No generic filler.",
    )
    coach_message: str = Field(
        "",
        description="Specific, useful message for the user (not generic motivational filler).",
    )
    estimated_duration_minutes: int = Field(20, ge=5, le=120, description="Total session duration in minutes, not one exercise")
    intensity: INTENSITY_LEVELS = Field("moderate", description="Session intensity level")
    warnings: str = Field("", description="Any session-level warnings or empty")
    exercises: list[ExerciseItem] = Field(default_factory=list, description="Session exercises; min 3 unless rest_day/recovery/mobility_snack/breathing_reset")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional extra data")


SYSTEM_PROMPT = """You are a fitness coach building a complete DAILY SESSION PLAN, not a single exercise suggestion.

OUTPUT RULES:
1. Generate a full daily session: session_goal, recommendation_type, reasoning_summary, coach_message, estimated_duration_minutes (total session, not one exercise), intensity, and recommended_exercises.
2. You MUST only select exercises from the CANDIDATE EXERCISES list. Use each exercise's "id" as exercise_id. Never invent exercises.
3. Minimum 3 exercises for a real training day. Only return 0 or 1 exercise when recommendation_type is exactly one of: rest_day, recovery, mobility_snack, breathing_reset.
4. Prefer 4–6 exercises when the recommendation is a true training day and enough candidates exist.
5. For isometric exercises (e.g. plank, side plank): use sets + duration_seconds (e.g. 30) + rest_seconds. Do NOT use a long "duration" for a single exercise as if it were the whole session.
6. estimated_duration_minutes must describe the WHOLE session (warm-up + all exercises + rest), not one exercise.
7. reasoning_summary MUST reference actual user context: sleep, energy, pain/fatigue, recent workout history, previous recommendations. It must not sound generic.
8. coach_message must be specific and useful (e.g. focus areas, form cues), not generic motivational filler.
9. Respect readiness_score and readiness_flags: if pain or low energy, choose lighter exercises and lower volume."""


def _build_user_message(state: RecommendationState) -> str:
    """Build the user-facing message with context and candidate exercises."""
    candidates = state.get("candidate_exercises") or []
    candidate_ids = [c["id"] for c in candidates]
    parts = [
        "Context:",
        f"- Date: {state.get('date')}",
        f"- Readiness score (0-1): {state.get('readiness_score')}",
        f"- Readiness flags: {state.get('readiness_flags')}",
        f"- Recommended session type: {state.get('recommendation_type')}",
        "",
        "Today's check-in (use for reasoning_summary and coach_message): " + json.dumps(state.get("checkin") or {}),
        "",
        "Recent workouts (reference in reasoning): " + json.dumps((state.get("recent_workouts") or [])[:5]),
        "",
        "Previous recommendations (reference in reasoning): " + json.dumps((state.get("previous_recommendations") or [])[:3]),
        "",
        "CANDIDATE EXERCISES (you must only use these; exercise_id must be one of " + str(candidate_ids) + "). Build a full session with at least 3 exercises unless type is rest_day/recovery/mobility_snack/breathing_reset:",
        json.dumps(candidates, indent=2),
    ]
    return "\n".join(parts)


def _exercise_item_to_dict(ex: ExerciseItem, i: int, candidate_ids: set[int], candidate_by_id: dict[int, dict]) -> dict[str, Any]:
    """Convert one ExerciseItem to API dict; enforce candidate_ids."""
    eid = ex.exercise_id
    if eid not in candidate_ids and candidate_ids:
        eid = next(iter(candidate_ids))
    out = {
        "exercise_id": eid,
        "name": (candidate_by_id.get(eid) or {}).get("name") or "",
        "sets": ex.sets,
        "rest_seconds": ex.rest_seconds,
        "notes": ex.notes or "",
        "position": i,
    }
    if ex.duration_seconds is not None:
        out["duration_seconds"] = ex.duration_seconds
        out["reps"] = None
    else:
        out["reps"] = ex.reps
        out["duration_seconds"] = None
    return out


def _plan_output_to_dict(
    parsed: RecommendationPlanOutput,
    candidate_ids: set[int],
    candidate_by_id: dict[int, dict],
    default_type: str,
) -> dict[str, Any]:
    """Convert Pydantic output to dict; enforce candidate_ids and include session fields."""
    exercises_out: list[dict[str, Any]] = []
    for i, ex in enumerate(parsed.exercises):
        eid = ex.exercise_id
        if eid not in candidate_ids and candidate_ids:
            eid = next(iter(candidate_ids))
        exercises_out.append(_exercise_item_to_dict(ex, i, candidate_ids, candidate_by_id))
    return {
        "session_goal": parsed.session_goal or "",
        "recommendation_type": parsed.recommendation_type or default_type,
        "reasoning_summary": parsed.reasoning_summary or "",
        "coach_message": parsed.coach_message or "",
        "estimated_duration_minutes": parsed.estimated_duration_minutes or 20,
        "intensity": parsed.intensity or "moderate",
        "warnings": parsed.warnings or "",
        "exercises": exercises_out,
        "metadata": parsed.metadata or {},
    }


def _parse_and_validate_raw(raw: str, candidate_ids: set[int], candidate_by_id: dict[int, dict], default_type: str) -> dict[str, Any] | None:
    """Strong schema validation: parse JSON then validate with Pydantic. Returns None on failure."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 1)[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
        raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        if hasattr(RecommendationPlanOutput, "model_validate"):
            parsed = RecommendationPlanOutput.model_validate(data)
        else:
            parsed = RecommendationPlanOutput.parse_obj(data)
        return _plan_output_to_dict(parsed, candidate_ids, candidate_by_id, default_type)
    except Exception:
        return None


def build_recommendation_plan_with_llm(state: RecommendationState) -> dict:
    """
    Produce a full daily session plan (session_goal, estimated_duration_minutes, intensity,
    recommended_exercises with min 3 for training days). Uses structured output when available.
    """
    candidates = state.get("candidate_exercises") or []
    candidate_ids = {c["id"] for c in candidates}
    candidate_by_id = {c["id"]: c for c in candidates}
    default_type = state.get("recommendation_type") or "recovery"

    if not candidates:
        return _empty_plan(default_type)

    try:
        from django.conf import settings
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        api_key = getattr(settings, "OPENAI_API_KEY", None) or ""
        if not api_key.strip():
            return _fallback_plan(state)

        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model, temperature=0.3, api_key=api_key)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_message(state)),
        ]

        if hasattr(llm, "with_structured_output"):
            structured_llm = llm.with_structured_output(RecommendationPlanOutput)
            parsed = structured_llm.invoke(messages)
            if isinstance(parsed, RecommendationPlanOutput):
                return _plan_output_to_dict(parsed, candidate_ids, candidate_by_id, default_type)

        response = llm.invoke(messages)
        raw = getattr(response, "content", None) or str(response)
        result = _parse_and_validate_raw(raw, candidate_ids, candidate_by_id, default_type)
        if result is not None:
            return result
    except Exception as e:
        logger.warning("LLM recommendation build failed: %s", e, exc_info=True)

    return _fallback_plan(state)


def _empty_plan(recommendation_type: str) -> dict[str, Any]:
    return {
        "session_goal": "Rest or light movement",
        "recommendation_type": recommendation_type,
        "reasoning_summary": "No candidate exercises available; rest day suggested.",
        "coach_message": "Rest or do light movement today.",
        "estimated_duration_minutes": 0,
        "intensity": "low",
        "warnings": "",
        "exercises": [],
        "metadata": {},
    }


def _fallback_plan(state: RecommendationState) -> dict[str, Any]:
    """Safe full-session fallback: 2-3 exercises when possible; else recovery/mobility_snack with 0-1."""
    candidates = state.get("candidate_exercises") or []
    rec_type = state.get("recommendation_type") or "recovery"
    # If only one or two candidates, treat as recovery/mobility_snack
    if len(candidates) <= 2:
        rec_type = "mobility_snack" if rec_type == "recovery" else rec_type
    safe = _get_safe_fallback_exercises_for_session(state)
    exercises = []
    for i, c in enumerate(safe[:6]):  # up to 6 for a small session
        exercises.append({
            "exercise_id": c["id"],
            "name": c.get("name") or "",
            "sets": 2,
            "reps": 10,
            "duration_seconds": None,
            "rest_seconds": 30,
            "notes": "Default prescription.",
            "position": i,
        })
    # If we have 2-3+ exercises, make it a proper session
    if len(exercises) >= 2:
        session_goal = "Light full session (fallback)"
        estimated_min = max(15, len(exercises) * 5)
    else:
        session_goal = "Recovery or mobility (fallback)"
        estimated_min = 10 if exercises else 0
    return {
        "session_goal": session_goal,
        "recommendation_type": rec_type,
        "reasoning_summary": "Recommendation generated with default parameters. Context was considered but LLM was unavailable.",
        "coach_message": "Train with control and listen to your body.",
        "estimated_duration_minutes": estimated_min,
        "intensity": "low_to_moderate",
        "warnings": "fallback_used",
        "exercises": exercises,
        "metadata": {},
    }


_SAFE_TAGS = {"mobility", "stretch", "recovery", "low_impact"}


def _get_safe_fallback_exercises_for_session(state: RecommendationState) -> list[dict]:
    """Return 2-6 safe exercises for fallback session (tags or intensity <= 3)."""
    candidates = state.get("candidate_exercises") or []
    catalog = state.get("exercise_catalog") or []
    pool = candidates if candidates else catalog
    if not pool:
        return []
    tier1 = [e for e in pool if any((t or "").lower() in _SAFE_TAGS for t in (e.get("tags") or []))]
    tier2 = [e for e in pool if int(e.get("intensity") or 10) <= 3]
    chosen = tier1 if tier1 else tier2
    chosen = sorted(chosen, key=lambda x: int(x.get("intensity") or 10))[:6]
    return chosen
