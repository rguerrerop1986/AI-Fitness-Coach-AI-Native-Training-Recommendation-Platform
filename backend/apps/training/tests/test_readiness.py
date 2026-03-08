"""Tests for deterministic readiness evaluation."""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model

from apps.training.models import DailyCheckIn, WorkoutLog, TrainingVideo
from apps.training.services.readiness import evaluate_readiness, ReadinessResult

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        role=User.Role.CLIENT,
    )


@pytest.fixture
def check_in_joint_pain(user):
    """Check-in with joint pain -> should force recovery."""
    return DailyCheckIn.objects.create(
        user=user,
        date=date.today(),
        joint_pain=True,
        energy_level=5,
        hours_sleep=7,
        sleep_quality=7,
    )


@pytest.fixture
def check_in_high_energy_good_sleep(user):
    """Check-in with high energy and good sleep -> higher score, allow intense."""
    return DailyCheckIn.objects.create(
        user=user,
        date=date.today(),
        joint_pain=False,
        energy_level=9,
        motivation_level=8,
        hours_sleep=8,
        sleep_quality=9,
        soreness_legs=2,
        soreness_arms=1,
    )


@pytest.mark.django_db
class TestReadinessWithJointPain:
    """When user reports joint pain, readiness should limit to recovery only."""

    def test_joint_pain_forces_recovery(self, check_in_joint_pain):
        result = evaluate_readiness(
            check_in=check_in_joint_pain,
            recent_logs=[],
            for_date=check_in_joint_pain.date,
        )
        assert isinstance(result, ReadinessResult)
        assert result.allowed_intensity == "recovery"
        assert any("joint" in w.lower() or "pain" in w.lower() for w in result.warnings)
        assert result.score <= 0.5


@pytest.mark.django_db
class TestReadinessHighEnergyGoodSleep:
    """When energy and sleep are good, score should be high and intensity allowed up to max."""

    def test_high_energy_good_sleep_allows_intense(self, check_in_high_energy_good_sleep):
        result = evaluate_readiness(
            check_in=check_in_high_energy_good_sleep,
            recent_logs=[],
            for_date=check_in_high_energy_good_sleep.date,
        )
        assert result.score >= 0.8
        assert result.allowed_intensity in ("intense", "max")
        assert len(result.warnings) == 0 or not any("joint" in w.lower() for w in result.warnings)


@pytest.mark.django_db
class TestReadinessRecentRPE:
    """High recent RPE should reduce allowed intensity."""

    def test_high_rpe_recent_reduces_intensity(self, user):
        video = TrainingVideo.objects.create(
            name="Test",
            program="Test",
            category=TrainingVideo.Category.CARDIO,
            difficulty=TrainingVideo.Difficulty.MEDIUM,
            is_active=True,
        )
        log = WorkoutLog.objects.create(
            user=user,
            date=date.today() - timedelta(days=1),
            video=video,
            rpe=9,
            completed=True,
        )
        check_in = DailyCheckIn.objects.create(
            user=user,
            date=date.today(),
            energy_level=7,
            sleep_quality=7,
        )
        result = evaluate_readiness(
            check_in=check_in,
            recent_logs=[log],
            for_date=date.today(),
        )
        assert result.allowed_intensity in ("intense", "moderate", "light", "recovery")
        # Should not be "max" after a 9 RPE yesterday
        assert result.allowed_intensity != "max" or result.score < 1.0
