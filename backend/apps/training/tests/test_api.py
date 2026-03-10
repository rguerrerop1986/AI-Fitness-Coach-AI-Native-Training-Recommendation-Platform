"""Tests for training API endpoints (recommendation generate with mocked OpenAI)."""
from datetime import date

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
        """Response has date, recommended_exercise, recommendation_plan, recommendation_type, etc."""
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
        assert data["recommended_exercise"]["id"] in [e.id for e in exercise_candidates]
        assert data["recommended_exercise"]["name"] in [e.name for e in exercise_candidates]
        assert data["recommended_exercise"]["muscle_group"] in [e.muscle_group for e in exercise_candidates]
        assert "recommendation_plan" in data
        assert data["recommendation_plan"]["exercises"]
        assert data["recommendation_type"] in (
            "recovery", "light", "moderate", "intense", "mobility", "mobility_snack", "breathing_reset",
            "upper_strength", "lower_strength", "cardio", "full_body", "core_recovery", "rest_day",
        )
        assert "recommended_exercises" in data
        assert "session_goal" in data
        assert "estimated_duration_minutes" in data
        assert "intensity" in data
        assert "reasoning_summary" in data
        assert "coach_message" in data

    def test_recommendation_persisted_with_recommended_exercise(
        self, api_client, user, exercise_candidates
    ):
        """TrainingRecommendation is saved with recommended_exercise FK and line items."""
        api_client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        rec = TrainingRecommendation.objects.get(user=user, date=date.today())
        assert rec.recommended_exercise_id in [e.id for e in exercise_candidates]
        from apps.training.models import TrainingRecommendationExercise
        line_items = list(TrainingRecommendationExercise.objects.filter(recommendation=rec))
        assert len(line_items) >= 1

    def test_empty_catalog_returns_200_with_rest_plan(self, api_client, user):
        """When Exercise catalog is empty, return 200 with a valid rest/recovery plan (0 exercises)."""
        resp = api_client.post(
            "/api/training/recommendations/generate/",
            {"date": date.today().isoformat()},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation_plan" in data
        assert data["recommendation_plan"]["recommendation_type"] in ("recovery", "rest_day", "mobility_snack")
        assert data["recommendation_plan"]["exercises"] == []
        assert data.get("recommended_exercise") is None

    def test_with_active_exercises_does_not_return_no_candidates(
        self, api_client, user, exercise_candidates
    ):
        """When active exercises exist, endpoint does not fail with no_candidates due to catalog."""
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
        """If we only have TrainingVideos and zero Exercises, we get a valid rest plan (0 exercises), not video-based candidates."""
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
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommendation_plan"]["exercises"] == []
        assert data.get("recommended_exercise") is None
