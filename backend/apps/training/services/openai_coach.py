"""
OpenAI-based coach service for LLM-driven exercise recommendation.

This module provides the LLM Reasoning Layer for single-exercise or candidate-selection
workflows:

  - Prompt construction: Builds a system prompt that constrains the model to choose
    exactly one exercise from the provided candidate list (by id), prioritizes safety
    (e.g., pain or fatigue → lighter option), and requires valid JSON output with
    recommended_exercise_id, recommendation_type, reasoning_summary, warnings, and
    coach_message.
  - Contextual data usage: The user message contains structured context (user state,
    recent logs, preferences) and the list of candidate exercise IDs. The model uses
    this context to align the recommendation with recovery and adherence.
  - Response handling: Parses JSON from the completion (strips markdown code blocks
    if present), validates that the returned id is in the candidate set, and falls
    back to a safe default (e.g., first candidate, moderate type) on parse or API
    failure.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_openai_client() -> Optional[OpenAI]:
    """Return OpenAI client if API key is set; otherwise None."""
    if not getattr(settings, "OPENAI_API_KEY", None) or not settings.OPENAI_API_KEY.strip():
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def recommend_workout_from_candidates(
    *,
    context: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Call the LLM to select one exercise from the candidate list using structured context.

    Recommendation logic: The model is instructed to choose only from the given
    candidate IDs, to prefer safer/lighter options when the user reports pain, poor
    sleep, or high fatigue, and to consider recent training logs to avoid repetition.
    Returns a dict with recommended_exercise_id, recommendation_type, reasoning_summary,
    warnings, and coach_message. candidates must include at least "id", "name",
    "muscle_group", "difficulty", "intensity", and "tags".
    """
    client = get_openai_client()
    candidate_ids = [c["id"] for c in candidates]

    if not client or not candidates:
        first_id = candidate_ids[0] if candidate_ids else None
        return {
            "recommended_exercise_id": first_id,
            "recommendation_type": "moderate",
            "reasoning_summary": "Recommendation unavailable (no API key or no candidates). Defaulting to first option."
            if first_id
            else "No candidate exercises available.",
            "warnings": "",
            "coach_message": "Check your setup and try again." if not first_id else "Train with control.",
        }

    system = """You are a fitness coaching assistant inside a workout app. Your job is to recommend exactly one exercise from the list of CANDIDATE exercises provided. You must only recommend an exercise that appears in that list (use its "id" in your response as recommended_exercise_id). Prioritize safety: if the user has pain, poor sleep, or high fatigue, be conservative and choose a lighter option. Consider the user's recent training logs and previous recommendations to avoid repetition and to match how they felt (e.g. if they had pain or felt drained, prefer recovery). You must respond with valid JSON only, no other text. Use this exact structure:
{
  "recommended_exercise_id": <integer id from candidate_exercises>,
  "recommendation_type": "recovery" | "light" | "moderate" | "intense" | "max",
  "reasoning_summary": "Short explanation in one or two sentences.",
  "warnings": "Optional warning or empty string.",
  "coach_message": "Short motivational or instructional message for the user."
}"""

    user_content = f"""Structured context for this user and date:
{json.dumps(context, indent=2)}

CANDIDATE exercises (you must choose exactly one by id). recommended_exercise_id must be one of: {candidate_ids}."""

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    temperature = getattr(settings, "OPENAI_TEMPERATURE", 0.3)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)
        eid = data.get("recommended_exercise_id")
        if eid is not None and eid not in candidate_ids:
            eid = candidate_ids[0]
        return {
            "recommended_exercise_id": eid,
            "recommendation_type": data.get("recommendation_type") or "moderate",
            "reasoning_summary": data.get("reasoning_summary") or "",
            "warnings": data.get("warnings") or "",
            "coach_message": data.get("coach_message") or "",
        }
    except Exception as e:
        logger.warning("OpenAI recommendation failed: %s", e, exc_info=True)
        return {
            "recommended_exercise_id": candidate_ids[0] if candidate_ids else None,
            "recommendation_type": "moderate",
            "reasoning_summary": f"Recommendation engine temporarily unavailable; defaulting to first safe option. ({e!s})",
            "warnings": "System fallback used.",
            "coach_message": "Train with control and listen to your body.",
        }
