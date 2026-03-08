"""Tests for recommendation context builder: includes previous recommendations and feedbacks."""
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn, TrainingRecommendation, WorkoutLog
from apps.training.selectors import get_recent_recommendations
from apps.training.services.recommendation_context import build_recommendation_context

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="ctxuser",
        email="ctx@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def exercise(db):
    return Exercise.objects.create(
        name="Test Exercise",
        muscle_group=Exercise.MuscleGroup.CORE,
        difficulty=Exercise.Difficulty.BEGINNER,
        intensity=5,
        tags=[],
        instructions="Do it.",
        is_active=True,
    )


@pytest.mark.django_db
class TestRecommendationContext:
    def test_context_includes_previous_recommendations(self, user, exercise):
        """Context includes previous_recommendations list."""
        TrainingRecommendation.objects.create(
            user=user,
            date=date.today() - timedelta(days=1),
            recommended_exercise=exercise,
            recommendation_type="moderate",
            reasoning_summary="Yesterday rec.",
            coach_message="Good.",
        )
        recs = list(get_recent_recommendations(user, days=14, before_date=date.today()))
        ctx = build_recommendation_context(
            user=user,
            for_date=date.today(),
            today_checkin=None,
            recent_workout_logs=[],
            recent_recommendations=recs,
            candidate_exercises=[exercise],
            readiness_summary="Ok",
        )
        assert "previous_recommendations" in ctx
        assert len(ctx["previous_recommendations"]) >= 1
        assert ctx["previous_recommendations"][0]["recommended_exercise_id"] == exercise.id
        assert ctx["previous_recommendations"][0]["recommendation_type"] == "moderate"

    def test_context_includes_candidate_exercises(self, user, exercise):
        """Context includes candidate_exercises with id, name, muscle_group, intensity, tags."""
        ctx = build_recommendation_context(
            user=user,
            for_date=date.today(),
            today_checkin=None,
            recent_workout_logs=[],
            recent_recommendations=[],
            candidate_exercises=[exercise],
            readiness_summary="",
        )
        assert "candidate_exercises" in ctx
        assert len(ctx["candidate_exercises"]) == 1
        c = ctx["candidate_exercises"][0]
        assert c["id"] == exercise.id
        assert c["name"] == exercise.name
        assert c["muscle_group"] == exercise.muscle_group
        assert c["intensity"] == exercise.intensity
        assert "tags" in c
