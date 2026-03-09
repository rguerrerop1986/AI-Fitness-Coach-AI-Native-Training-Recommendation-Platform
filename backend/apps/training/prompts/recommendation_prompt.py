"""
Prompt and LangChain structured output for training recommendations.
Uses Pydantic models and with_structured_output (or strong schema validation fallback).
Rules: only use provided candidate exercises; never invent exercises; respect readiness and pain.
"""
import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from apps.training.graph.state import RecommendationState

logger = logging.getLogger(__name__)

# ----- Pydantic models for structured output -----

RECOMMENDATION_TYPES = Literal[
    "recovery",
    "mobility",
    "upper_strength",
    "lower_strength",
    "cardio",
    "full_body",
    "rest_day",
]


class ExerciseItem(BaseModel):
    """One exercise in the recommendation plan."""

    exercise_id: int = Field(..., description="ID from candidate list")
    sets: int = Field(2, ge=1, le=20, description="Number of sets")
    reps: int = Field(10, ge=1, le=50, description="Reps per set")
    rest_seconds: int = Field(60, ge=0, le=600, description="Rest between sets (seconds)")
    notes: str = Field("", description="Optional note")
    position: int = Field(0, ge=0, description="Order in plan")


class RecommendationPlanOutput(BaseModel):
    """Full recommendation plan from the LLM."""

    recommendation_type: RECOMMENDATION_TYPES = Field(
        "recovery",
        description="Session type",
    )
    reasoning_summary: str = Field("", description="Why this plan fits today")
    coach_message: str = Field("", description="Short message for the user")
    exercises: list[ExerciseItem] = Field(default_factory=list, description="Selected exercises")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional extra data")


SYSTEM_PROMPT = """You are a fitness coach inside a workout app. Your job is to build a single daily workout recommendation.

RULES (strict):
- You MUST only select exercises from the CANDIDATE EXERCISES list provided. Use each exercise's "id" as exercise_id.
- NEVER invent or add exercises that are not in the candidate list.
- Respect the user's readiness_score and readiness_flags: if pain or low energy, choose lighter exercises and lower volume.

For rest_day or recovery, you may use 1-2 very light exercises or empty exercises. Keep total sets reasonable (e.g. under 25)."""


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
        "Today's check-in (if any): " + json.dumps(state.get("checkin") or {}),
        "",
        "Recent workouts (last 5): " + json.dumps((state.get("recent_workouts") or [])[:5]),
        "",
        "Previous recommendations (last 3): " + json.dumps((state.get("previous_recommendations") or [])[:3]),
        "",
        "CANDIDATE EXERCISES (you must only use these; exercise_id must be one of " + str(candidate_ids) + "):",
        json.dumps(candidates, indent=2),
    ]
    return "\n".join(parts)


def _plan_output_to_dict(
    parsed: RecommendationPlanOutput,
    candidate_ids: set[int],
    default_type: str,
) -> dict[str, Any]:
    """Convert Pydantic output to dict and enforce candidate_ids on exercise_id."""
    exercises_out: list[dict[str, Any]] = []
    for i, ex in enumerate(parsed.exercises):
        eid = ex.exercise_id
        if eid not in candidate_ids and candidate_ids:
            eid = next(iter(candidate_ids))
        exercises_out.append({
            "exercise_id": eid,
            "sets": ex.sets,
            "reps": ex.reps,
            "rest_seconds": ex.rest_seconds,
            "notes": ex.notes or "",
            "position": i,
        })
    return {
        "recommendation_type": parsed.recommendation_type or default_type,
        "reasoning_summary": parsed.reasoning_summary or "",
        "coach_message": parsed.coach_message or "",
        "exercises": exercises_out,
        "metadata": parsed.metadata or {},
    }


def _parse_and_validate_raw(raw: str, candidate_ids: set[int], default_type: str) -> dict[str, Any] | None:
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
        # Pydantic v2: model_validate; v1: parse_obj
        if hasattr(RecommendationPlanOutput, "model_validate"):
            parsed = RecommendationPlanOutput.model_validate(data)
        else:
            parsed = RecommendationPlanOutput.parse_obj(data)
        return _plan_output_to_dict(parsed, candidate_ids, default_type)
    except Exception:
        return None


def build_recommendation_plan_with_llm(state: RecommendationState) -> dict:
    """
    Use LangChain structured output (Pydantic) to produce recommendation_plan from state.
    Uses ChatOpenAI.with_structured_output(RecommendationPlanOutput) when available;
    otherwise parses raw response and validates with RecommendationPlanOutput.model_validate().
    Returns a dict with recommendation_type, reasoning_summary, coach_message, exercises, metadata.
    """
    candidates = state.get("candidate_exercises") or []
    candidate_ids = {c["id"] for c in candidates}
    default_type = state.get("recommendation_type") or "recovery"

    if not candidates:
        return {
            "recommendation_type": default_type,
            "reasoning_summary": "No candidate exercises available; rest day suggested.",
            "coach_message": "Rest or do light movement today.",
            "exercises": [],
            "metadata": {},
        }

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

        # Prefer with_structured_output when available
        if hasattr(llm, "with_structured_output"):
            structured_llm = llm.with_structured_output(RecommendationPlanOutput)
            parsed = structured_llm.invoke(messages)
            if isinstance(parsed, RecommendationPlanOutput):
                return _plan_output_to_dict(parsed, candidate_ids, default_type)

        # Fallback: raw invoke + strong schema validation
        response = llm.invoke(messages)
        raw = getattr(response, "content", None) or str(response)
        result = _parse_and_validate_raw(raw, candidate_ids, default_type)
        if result is not None:
            return result
    except Exception as e:
        logger.warning("LLM recommendation build failed: %s", e, exc_info=True)

    return _fallback_plan(state)


def _fallback_plan(state: RecommendationState) -> dict:
    """Safe plan when LLM is unavailable or validation fails."""
    candidates = state.get("candidate_exercises") or []
    exercises = []
    for i, c in enumerate(candidates[:5]):
        exercises.append({
            "exercise_id": c["id"],
            "sets": 2,
            "reps": 10,
            "rest_seconds": 60,
            "notes": "Default prescription.",
            "position": i,
        })
    return {
        "recommendation_type": state.get("recommendation_type") or "recovery",
        "reasoning_summary": "Recommendation generated with default parameters.",
        "coach_message": "Train with control and listen to your body.",
        "exercises": exercises,
        "metadata": {},
    }
