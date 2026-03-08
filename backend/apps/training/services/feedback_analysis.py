"""
Post-workout feedback analysis via OpenAI: summary, coach_comment, tomorrow_hint.
"""
import json
import logging
from typing import Any, Dict, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_openai_client() -> Optional[OpenAI]:
    """Return OpenAI client if API key is set; otherwise None."""
    if not getattr(settings, "OPENAI_API_KEY", None) or not settings.OPENAI_API_KEY.strip():
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def analyze_workout_feedback(
    *,
    video_name: str,
    completed: bool,
    rpe: Optional[int] = None,
    satisfaction: Optional[int] = None,
    felt_strong: Optional[bool] = None,
    felt_drained: Optional[bool] = None,
    recovery_fast: Optional[bool] = None,
    pain_during_workout: bool = False,
    pain_notes: str = "",
    body_feedback: str = "",
    emotional_feedback: str = "",
) -> Dict[str, Any]:
    """
    Use OpenAI to generate:
    - summary: short recap of the session
    - coach_comment: brief coach-style comment
    - tomorrow_hint: hint for next day's training decision
    Returns dict with those keys; on failure returns fallback text.
    """
    client = get_openai_client()
    if not client:
        return {
            "summary": "Feedback recorded. No analysis (OpenAI not configured).",
            "coach_comment": "Keep consistent and listen to your body.",
            "tomorrow_hint": "Do your next check-in tomorrow to get a recommendation.",
        }

    user_content = f"""Workout: {video_name}
Completed: {completed}
RPE: {rpe if rpe is not None else 'N/A'}
Satisfaction: {satisfaction if satisfaction is not None else 'N/A'}
Felt strong: {felt_strong if felt_strong is not None else 'N/A'}
Felt drained: {felt_drained if felt_drained is not None else 'N/A'}
Recovery fast: {recovery_fast if recovery_fast is not None else 'N/A'}
Pain during workout: {pain_during_workout}
Pain notes: {pain_notes or 'None'}
Body feedback: {body_feedback or 'None'}
Emotional feedback: {emotional_feedback or 'None'}

Respond with valid JSON only:
{{
  "summary": "One or two sentence recap of the session.",
  "coach_comment": "Brief coach-style comment.",
  "tomorrow_hint": "Short hint for tomorrow's training (recovery vs intensity)."
}}"""

    system = "You are a fitness coach assistant. Analyze the workout feedback and respond with valid JSON only (summary, coach_comment, tomorrow_hint)."

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
        return {
            "summary": data.get("summary") or "",
            "coach_comment": data.get("coach_comment") or "",
            "tomorrow_hint": data.get("tomorrow_hint") or "",
        }
    except Exception as e:
        logger.warning("OpenAI feedback analysis failed: %s", e, exc_info=True)
        return {
            "summary": "Feedback recorded.",
            "coach_comment": "Keep consistent and listen to your body.",
            "tomorrow_hint": "Do your check-in tomorrow for a recommendation.",
        }
