"""Tests for video selector: excludes explosive / heavy leg when pain or leg fatigue."""
import pytest
from django.contrib.auth import get_user_model

from apps.training.models import DailyCheckIn, TrainingVideo
from apps.training.services.readiness import ReadinessResult
from apps.training.services.video_selector import get_candidate_videos

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
def recovery_video(db):
    return TrainingVideo.objects.create(
        name="Cardio Recovery",
        program="Insanity",
        category=TrainingVideo.Category.RECOVERY,
        difficulty=TrainingVideo.Difficulty.LOW,
        explosive=False,
        stresses_legs=True,
        is_active=True,
    )


@pytest.fixture
def explosive_leg_video(db):
    return TrainingVideo.objects.create(
        name="Max Interval Plyo",
        program="Insanity",
        category=TrainingVideo.Category.PLYOMETRICS,
        difficulty=TrainingVideo.Difficulty.MAX,
        explosive=True,
        stresses_legs=True,
        is_active=True,
    )


@pytest.fixture
def moderate_video(db):
    return TrainingVideo.objects.create(
        name="Cardio Power",
        program="Insanity",
        category=TrainingVideo.Category.MIXED,
        difficulty=TrainingVideo.Difficulty.MEDIUM,
        explosive=False,
        stresses_legs=True,
        is_active=True,
    )


@pytest.mark.django_db
class TestVideoSelectorExcludesExplosiveWithLegPain:
    """When check-in has joint pain or high leg soreness, explosive / heavy leg videos excluded."""

    def test_joint_pain_excludes_explosive(
        self, user, recovery_video, explosive_leg_video, moderate_video
    ):
        readiness = ReadinessResult(
            score=0.3,
            warnings=["Joint pain reported."],
            allowed_intensity="recovery",
            payload={},
        )
        check_in = DailyCheckIn.objects.create(
            user=user,
            date=__import__("datetime").date.today(),
            joint_pain=True,
            soreness_legs=5,
        )
        candidates = get_candidate_videos(readiness, check_in, limit=5)
        ids = [c.id for c in candidates]
        # Recovery only: should include recovery video, not max plyo
        assert recovery_video.id in ids
        assert explosive_leg_video.id not in ids

    def test_high_leg_soreness_excludes_explosive_legs(
        self, user, recovery_video, explosive_leg_video, moderate_video
    ):
        readiness = ReadinessResult(
            score=0.6,
            warnings=["High leg soreness."],
            allowed_intensity="moderate",
            payload={},
        )
        check_in = DailyCheckIn.objects.create(
            user=user,
            date=__import__("datetime").date.today(),
            joint_pain=False,
            soreness_legs=7,
        )
        candidates = get_candidate_videos(readiness, check_in, limit=5)
        ids = [c.id for c in candidates]
        # Explosive video (stresses_legs + high/max) should be excluded
        assert explosive_leg_video.id not in ids
        # Recovery or moderate should be in
        assert any(c.id in (recovery_video.id, moderate_video.id) for c in candidates)
