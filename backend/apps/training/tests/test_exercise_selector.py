"""Tests for exercise selector: uses catalogs.Exercise, filters by readiness and check-in."""
import pytest
from django.contrib.auth import get_user_model

from apps.catalogs.models import Exercise
from apps.training.models import DailyCheckIn
from apps.training.services.exercise_selector import get_candidate_exercises
from apps.training.services.readiness import ReadinessResult

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="seluser",
        email="sel@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def recovery_exercise(db):
    return Exercise.objects.create(
        name="Cardio Recovery",
        muscle_group=Exercise.MuscleGroup.CARDIO,
        difficulty=Exercise.Difficulty.BEGINNER,
        intensity=3,
        tags=[],
        instructions="Light.",
        is_active=True,
    )


@pytest.fixture
def high_intensity_lower_body(db):
    return Exercise.objects.create(
        name="Max Legs",
        muscle_group=Exercise.MuscleGroup.QUADS,
        difficulty=Exercise.Difficulty.ADVANCED,
        intensity=8,
        tags=[],
        instructions="Heavy.",
        is_active=True,
    )


@pytest.fixture
def moderate_exercise(db):
    return Exercise.objects.create(
        name="Cardio Power",
        muscle_group=Exercise.MuscleGroup.CARDIO,
        difficulty=Exercise.Difficulty.INTERMEDIATE,
        intensity=6,
        tags=[],
        instructions="Moderate.",
        is_active=True,
    )


@pytest.mark.django_db
class TestExerciseSelectorUsesCatalog:
    """Selector uses apps.catalogs.models.Exercise, not TrainingVideo."""

    def test_returns_exercises_not_videos(self, user, recovery_exercise, moderate_exercise):
        """Candidates are Exercise instances from catalogs."""
        readiness = ReadinessResult(
            score=0.7,
            warnings=[],
            allowed_intensity="moderate",
            payload={},
        )
        candidates = get_candidate_exercises(readiness, None, limit=5)
        assert len(candidates) >= 1
        for c in candidates:
            assert isinstance(c, Exercise)
            assert c.muscle_group is not None
            assert 1 <= c.intensity <= 10

    def test_joint_pain_limits_to_low_intensity(
        self, user, recovery_exercise, high_intensity_lower_body, moderate_exercise
    ):
        """With joint pain (recovery only), only low-intensity exercises included."""
        readiness = ReadinessResult(
            score=0.3,
            warnings=["Joint pain."],
            allowed_intensity="recovery",
            payload={},
        )
        check_in = DailyCheckIn.objects.create(
            user=user,
            date=__import__("datetime").date.today(),
            joint_pain=True,
        )
        candidates = get_candidate_exercises(readiness, check_in, limit=5)
        ids = [c.id for c in candidates]
        assert recovery_exercise.id in ids
        assert high_intensity_lower_body.id not in ids

    def test_high_leg_soreness_excludes_high_intensity_lower_body(
        self, user, recovery_exercise, high_intensity_lower_body, moderate_exercise
    ):
        """With high leg soreness, high-intensity lower body excluded."""
        readiness = ReadinessResult(
            score=0.6,
            warnings=[],
            allowed_intensity="moderate",
            payload={},
        )
        check_in = DailyCheckIn.objects.create(
            user=user,
            date=__import__("datetime").date.today(),
            joint_pain=False,
            soreness_legs=7,
        )
        candidates = get_candidate_exercises(readiness, check_in, limit=5)
        ids = [c.id for c in candidates]
        assert high_intensity_lower_body.id not in ids
        assert recovery_exercise.id in ids or moderate_exercise.id in ids
