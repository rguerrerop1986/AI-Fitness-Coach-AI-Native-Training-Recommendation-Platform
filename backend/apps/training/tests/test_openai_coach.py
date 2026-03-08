"""Tests for OpenAI coach: receives structured context and candidate_exercises."""
from unittest.mock import MagicMock, patch

import pytest

from apps.training.services.openai_coach import recommend_workout_from_candidates


class TestOpenAICoachReceivesStructuredContext:
    def test_openai_receives_candidate_exercises_in_context(self):
        """LLM is called with context that includes candidate_exercises and must choose from them."""
        context = {
            "user": {"id": 1, "name": "Test User"},
            "date": "2026-03-07",
            "today_checkin": {"energy_level": 7},
            "recent_training_logs": [],
            "recent_feedbacks": [],
            "previous_recommendations": [],
            "candidate_exercises": [
                {"id": 10, "name": "Recovery Stretch", "muscle_group": "cardio", "difficulty": "beginner", "intensity": 3, "tags": []},
                {"id": 20, "name": "Cardio Light", "muscle_group": "cardio", "difficulty": "intermediate", "intensity": 5, "tags": []},
            ],
            "readiness_summary": "Score 0.8, allowed intensity: moderate.",
        }
        candidates = context["candidate_exercises"]

        with patch("apps.training.services.openai_coach.get_openai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='{"recommended_exercise_id": 20, "recommendation_type": "moderate", "reasoning_summary": "Good.", "warnings": "", "coach_message": "Go."}'
                        )
                    )
                ]
            )
            result = recommend_workout_from_candidates(context=context, candidates=candidates)

        assert result["recommended_exercise_id"] == 20
        assert result["recommendation_type"] == "moderate"
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        user_content = next(m["content"] for m in messages if m["role"] == "user")
        assert "candidate_exercises" in user_content
        assert "previous_recommendations" in user_content
        assert "10" in user_content and "20" in user_content
