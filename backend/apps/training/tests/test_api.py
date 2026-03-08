"""Tests for training API endpoints (recommendation generate with mocked OpenAI)."""
from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation, TrainingVideo

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="apiuser",
        email="api@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
        first_name="Raul",
        last_name="Guerrero",
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def exercise_candidates(db):
    """Active exercises in catalog (source of truth for recommendations)."""
    e1 = Exercise.objects.create(
        name="Cardio Recovery",
        muscle_group=Exercise.MuscleGroup.CARDIO,
        difficulty=Exercise.Difficulty.BEGINNER,
        intensity=3,
        tags=["low_impact", "mobility"],
        instructions="Light movement.",
        is_active=True,
    )
    e2 = Exercise.objects.create(
        name="Cardio Power",
        muscle_group=Exercise.MuscleGroup.CARDIO,
        difficulty=Exercise.Difficulty.INTERMEDIATE,
        intensity=6,
        tags=[],
        instructions="Moderate cardio.",
        is_active=True,
    )
    return [e1, e2]


@pytest.mark.django_db
class TestGenerateRecommendationEndpoint:
    """POST /api/training/recommendations/generate/ with mocked OpenAI."""

    def test_generate_returns_200_and_recommended_exercise(
        self, api_client, user, exercise_candidates
    ):
        """With OpenAI mocked, response has date, recommended_exercise, recommendation_type, etc."""
        with patch(
            "apps.training.services.recommendation_service.recommend_workout_from_candidates"
        ) as mock_llm:
            mock_llm.return_value = {
                "recommended_exercise_id": exercise_candidates[1].id,
                "recommendation_type": "moderate",
                "reasoning_summary": "Good energy, moderate fits.",
                "warnings": "",
                "coach_message": "Train with control.",
            }
            resp = api_client.post(
                "/api/training/recommendations/generate/",
                {"date": date.today().isoformat()},
                format="json",
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "recommended_exercise" in data
        assert data["recommended_exercise"] is not None
        assert data["recommended_exercise"]["id"] == exercise_candidates[1].id
        assert data["recommended_exercise"]["name"] == "Cardio Power"
        assert data["recommended_exercise"]["muscle_group"] == "cardio"
        assert data["recommendation_type"] == "moderate"
        assert "reasoning_summary" in data
        assert "coach_message" in data

    def test_recommendation_persisted_with_recommended_exercise(
        self, api_client, user, exercise_candidates
    ):
        """TrainingRecommendation is saved with recommended_exercise FK."""
        with patch(
            "apps.training.services.recommendation_service.recommend_workout_from_candidates"
        ) as mock_llm:
            mock_llm.return_value = {
                "recommended_exercise_id": exercise_candidates[0].id,
                "recommendation_type": "recovery",
                "reasoning_summary": "Recovery day.",
                "warnings": "",
                "coach_message": "Take it easy.",
            }
            api_client.post(
                "/api/training/recommendations/generate/",
                {"date": date.today().isoformat()},
                format="json",
            )
        rec = TrainingRecommendation.objects.get(user=user, date=date.today())
        assert rec.recommended_exercise_id == exercise_candidates[0].id
        assert rec.recommended_exercise.name == "Cardio Recovery"

    def test_no_candidates_only_when_no_eligible_exercises(self, api_client, user):
        """no_candidates returned only when Exercise catalog has no eligible exercises (e.g. recovery + all high intensity)."""
        # No check-in, no exercises in DB -> no candidates
        resp = api_client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data.get("error") == "no_candidates"
        assert data.get("recommended_exercise") is None

    def test_with_active_exercises_does_not_return_no_candidates(
        self, api_client, user, exercise_candidates
    ):
        """When active exercises exist, endpoint does not fail with no_candidates due to catalog."""
        with patch(
            "apps.training.services.recommendation_service.recommend_workout_from_candidates"
        ) as mock_llm:
            mock_llm.return_value = {
                "recommended_exercise_id": exercise_candidates[0].id,
                "recommendation_type": "light",
                "reasoning_summary": "Ok.",
                "warnings": "",
                "coach_message": "Go.",
            }
            resp = api_client.post(
                "/api/training/recommendations/generate/",
                {"date": date.today().isoformat()},
                format="json",
            )
        assert resp.status_code == 200
        assert resp.json().get("error") is None
        assert resp.json().get("recommended_exercise") is not None

    def test_generate_requires_auth(self, exercise_candidates):
        """Without JWT, returns 401."""
        client = APIClient()
        resp = client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        assert resp.status_code == 401

    def test_generate_validates_date(self, api_client):
        """Invalid date returns 400."""
        resp = api_client.post(
            "/api/training/recommendations/generate/",
            {"date": "not-a-date"},
            format="json",
        )
        assert resp.status_code == 400

    def test_recommendation_uses_exercise_catalog_not_training_video(self, api_client, user):
        """If we only have TrainingVideos and zero Exercises, we get no_candidates. Fails if flow used TrainingVideo for candidates."""
        TrainingVideo.objects.create(
            name="Legacy Video",
            program="Insanity",
            category=TrainingVideo.Category.RECOVERY,
            difficulty=TrainingVideo.Difficulty.LOW,
            is_active=True,
        )
        assert Exercise.objects.filter(is_active=True).count() == 0
        resp = api_client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json().get("error") == "no_candidates"
        assert resp.json().get("recommended_exercise") is None
