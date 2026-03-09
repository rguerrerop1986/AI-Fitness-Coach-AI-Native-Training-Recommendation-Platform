"""
Prompt and LangChain structured output for training recommendations.
Rules: only use provided candidate exercises; never invent exercises; respect readiness and pain; return JSON only.
"""
import json
import logging
from typing import Any

from apps.training.graph.state import RecommendationState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fitness coach inside a workout app. Your job is to build a single daily workout recommendation.

RULES (strict):
- You MUST only select exercises from the CANDIDATE EXERCISES list provided. Use each exercise's "id" as exercise_id.
- NEVER invent or add exercises that are not in the candidate list.
- Respect the user's readiness_score and readiness_flags: if pain or low energy, choose lighter exercises and lower volume.
- Return valid JSON only, no markdown or extra text.

Output structure (use exactly these keys):
{
  "recommendation_type": "recovery" | "mobility" | "upper_strength" | "lower_strength" | "cardio" | "full_body" | "rest_day",
  "reasoning_summary": "One or two sentences explaining why this plan fits the user today.",
  "coach_message": "Short motivational or instructional message for the user.",
  "exercises": [
    {
      "exercise_id": <integer id from candidate list>,
      "sets": 2-5,
      "reps": 8-15,
      "rest_seconds": 30-120,
      "notes": "Optional short note.",
      "position": 0
    }
  ]
}

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
        "",
        "Respond with JSON only (recommendation_type, reasoning_summary, coach_message, exercises).",
    ]
    return "\n".join(parts)


def build_recommendation_plan_with_llm(state: RecommendationState) -> dict:
    """
    Use LangChain with structured output to produce recommendation_plan from state.
    Only selects from candidate_exercises; generates sets/reps/rest, reasoning_summary, coach_message.
    Returns a dict with recommendation_type, reasoning_summary, coach_message, exercises (list of {exercise_id, sets, reps, rest_seconds, notes, position}).
    If LLM is unavailable or fails, returns a safe fallback plan using first candidates.
    """
    candidates = state.get("candidate_exercises") or []
    if not candidates:
        return {
            "recommendation_type": state.get("recommendation_type") or "recovery",
            "reasoning_summary": "No candidate exercises available; rest day suggested.",
            "coach_message": "Rest or do light movement today.",
            "exercises": [],
        }

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        from django.conf import settings
        api_key = getattr(settings, "OPENAI_API_KEY", None) or ""
        if not api_key.strip():
            return _fallback_plan(state)

        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model, temperature=0.3, api_key=api_key)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_message(state)),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)

        # Ensure exercises only reference candidate IDs
        candidate_ids = {c["id"] for c in candidates}
        exercises = data.get("exercises") or []
        for i, ex in enumerate(exercises):
            eid = ex.get("exercise_id")
            if eid not in candidate_ids:
                ex["exercise_id"] = list(candidate_ids)[0] if candidate_ids else None
            ex["position"] = i
        return {
            "recommendation_type": data.get("recommendation_type") or state.get("recommendation_type") or "moderate",
            "reasoning_summary": data.get("reasoning_summary") or "",
            "coach_message": data.get("coach_message") or "",
            "exercises": exercises,
            "metadata": data.get("metadata") or {},
        }
    except Exception as e:
        logger.warning("LLM recommendation build failed: %s", e, exc_info=True)
        return _fallback_plan(state)


def _fallback_plan(state: RecommendationState) -> dict:
    """Safe plan when LLM is unavailable or errors."""
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
