"""Training content selector abstraction for recommendation payloads."""

from __future__ import annotations

from dataclasses import dataclass

from apps.training.models import TrainingVideo


@dataclass(frozen=True)
class SelectedTrainingContent:
    intensity_level: str
    duration_minutes: int
    recommended_video_id: int | None = None


class TrainingSelector:
    """Maps recommendation intent to concrete session defaults."""

    DEFAULTS: dict[str, tuple[str, int]] = {
        "insanity_max": ("high", 55),
        "insanity_moderate": ("moderate", 40),
        "strength_upper": ("high", 45),
        "strength_lower": ("high", 45),
        "hybrid_training": ("moderate", 42),
        "mobility_recovery": ("recovery", 25),
        "cardio_light": ("low", 30),
        "full_rest": ("recovery", 0),
    }

    CATEGORY_MAP: dict[str, str] = {
        "insanity_max": TrainingVideo.Category.PLYOMETRICS,
        "insanity_moderate": TrainingVideo.Category.CARDIO,
        "strength_upper": TrainingVideo.Category.STRENGTH,
        "strength_lower": TrainingVideo.Category.STRENGTH,
        "hybrid_training": TrainingVideo.Category.MIXED,
        "mobility_recovery": TrainingVideo.Category.RECOVERY,
        "cardio_light": TrainingVideo.Category.CARDIO,
    }

    def select(self, recommendation_type: str) -> SelectedTrainingContent:
        intensity_level, duration = self.DEFAULTS.get(recommendation_type, ("moderate", 35))
        video_id = self._pick_video_id(recommendation_type)
        return SelectedTrainingContent(
            intensity_level=intensity_level,
            duration_minutes=duration,
            recommended_video_id=video_id,
        )

    def _pick_video_id(self, recommendation_type: str) -> int | None:
        category = self.CATEGORY_MAP.get(recommendation_type)
        if not category:
            return None
        video = (
            TrainingVideo.objects.filter(is_active=True, category=category)
            .order_by("difficulty", "id")
            .first()
        )
        return video.id if video else None
