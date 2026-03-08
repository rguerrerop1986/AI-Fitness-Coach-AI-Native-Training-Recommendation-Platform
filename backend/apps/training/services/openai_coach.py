"""
OpenAI-based coach: given context and candidate videos, returns a single recommendation as JSON.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from openai import OpenAI

from apps.training.models import TrainingVideo

logger = logging.getLogger(__name__)


def get_openai_client() -> Optional[OpenAI]:
    """Return OpenAI client if API key is set; otherwise None."""
    if not getattr(settings, "OPENAI_API_KEY", None) or not settings.OPENAI_API_KEY.strip():
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _build_candidates_payload(candidates: List[TrainingVideo]) -> List[Dict[str, Any]]:
    """Build a minimal payload of candidate videos for the prompt."""
    return [
        {
            "id": v.id,
            "name": v.name,
            "category": v.category,
            "difficulty": v.difficulty,
            "duration_minutes": v.duration_minutes,
            "description": (v.description or "")[:200],
        }
        for v in candidates
    ]


def recommend_workout_from_candidates(
    *,
    check_in_summary: str,
    recent_history_summary: str,
    readiness_summary: str,
    candidates: List[TrainingVideo],
) -> Dict[str, Any]:
    """
    Call OpenAI to pick one workout from the candidate list and return structured JSON.
    Returns dict with: recommended_workout_id, recommendation_type, reasoning_summary, warnings, coach_message.
    On failure or missing API key, returns a fallback recommendation (first candidate, type moderate).
    """
    client = get_openai_client()
    if not client or not candidates:
        # Fallback: first candidate, moderate
        first = candidates[0] if candidates else None
        return {
            "recommended_workout_id": first.id if first else None,
            "recommendation_type": "moderate",
            "reasoning_summary": "Recommendation unavailable (no API key or no candidates). Defaulting to first option."
            if first
            else "No candidate videos available.",
            "warnings": "",
            "coach_message": "Check your setup and try again." if not first else "Train with control.",
        }

    candidates_payload = _build_candidates_payload(candidates)
    candidate_ids = [c["id"] for c in candidates_payload]

    system = """You are a fitness coaching assistant inside a workout app. Your job is to recommend exactly one workout from the list of CANDIDATE workouts provided. You must only recommend a workout that appears in that list (use its "id" in your response). Prioritize safety: if the user has pain, poor sleep, or high fatigue, be conservative and choose a lighter option. You must respond with valid JSON only, no other text. Use this exact structure:
{
  "recommended_workout_id": <integer id from candidates>,
  "recommendation_type": "recovery" | "light" | "moderate" | "intense" | "max",
  "reasoning_summary": "Short explanation in one or two sentences.",
  "warnings": "Optional warning or empty string.",
  "coach_message": "Short motivational or instructional message for the user."
}"""

    user_content = f"""Today's check-in: {check_in_summary}

Recent workout history: {recent_history_summary}

Readiness evaluation: {readiness_summary}

CANDIDATE workouts (you must choose exactly one by id):
{json.dumps(candidates_payload, indent=2)}

Respond with JSON only. recommended_workout_id must be one of: {candidate_ids}."""

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
        # Handle possible markdown code block
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)
        # Validate and coerce
        wid = data.get("recommended_workout_id")
        if wid is not None and wid not in candidate_ids:
            wid = candidate_ids[0]
        return {
            "recommended_workout_id": wid,
            "recommendation_type": data.get("recommendation_type") or "moderate",
            "reasoning_summary": data.get("reasoning_summary") or "",
            "warnings": data.get("warnings") or "",
            "coach_message": data.get("coach_message") or "",
        }
    except Exception as e:
        logger.warning("OpenAI recommendation failed: %s", e, exc_info=True)
        return {
            "recommended_workout_id": candidate_ids[0] if candidate_ids else None,
            "recommendation_type": "moderate",
            "reasoning_summary": f"Recommendation engine temporarily unavailable; defaulting to first safe option. ({e!s})",
            "warnings": "System fallback used.",
            "coach_message": "Train with control and listen to your body.",
        }
