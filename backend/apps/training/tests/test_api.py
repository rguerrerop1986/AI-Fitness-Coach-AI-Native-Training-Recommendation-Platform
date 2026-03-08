"""Tests for training API endpoints (recommendation generate with mocked OpenAI)."""
from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.training.models import TrainingVideo, DailyCheckIn

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="apiuser",
        email="api@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def video_candidates(db):
    v1 = TrainingVideo.objects.create(
        name="Cardio Recovery",
        program="Insanity",
        category=TrainingVideo.Category.RECOVERY,
        difficulty=TrainingVideo.Difficulty.LOW,
        is_active=True,
    )
    v2 = TrainingVideo.objects.create(
        name="Cardio Power and Resistance",
        program="Insanity",
        category=TrainingVideo.Category.MIXED,
        difficulty=TrainingVideo.Difficulty.MEDIUM,
        is_active=True,
    )
    return [v1, v2]


@pytest.mark.django_db
class TestGenerateRecommendationEndpoint:
    """POST /api/training/recommendations/generate/ with mocked OpenAI."""

    def test_generate_returns_200_and_structure(
        self, api_client, user, video_candidates
    ):
        """With OpenAI mocked, response has date, recommended_video, recommendation_type, etc."""
        with patch(
            "apps.training.services.recommendation_service.recommend_workout_from_candidates"
        ) as mock_llm:
            mock_llm.return_value = {
                "recommended_workout_id": video_candidates[1].id,
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
        assert "recommended_video" in data
        assert data["recommended_video"] is not None
        assert data["recommended_video"]["id"] == video_candidates[1].id
        assert data["recommended_video"]["name"] == "Cardio Power and Resistance"
        assert data["recommendation_type"] == "moderate"
        assert "reasoning_summary" in data
        assert "coach_message" in data

    def test_generate_requires_auth(self, video_candidates):
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
