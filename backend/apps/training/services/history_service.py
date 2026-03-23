"""Recent history helpers used by adaptive recommendation logic."""

from __future__ import annotations

from datetime import date, timedelta

from apps.training.models import CompletedWorkout, TrainingRecommendation


class HistoryService:
    """Encapsulates last-7-days behavior reads and simple aggregates."""

    def get_recent_summary(self, user_id: int, target_date: date, days: int = 7) -> dict:
        start_date = target_date - timedelta(days=days)
        workouts = list(
            CompletedWorkout.objects.filter(user_id=user_id, date__gte=start_date, date__lt=target_date).order_by("-date")
        )
        recommendations = list(
            TrainingRecommendation.objects.filter(user_id=user_id, date__gte=start_date, date__lt=target_date).order_by("-date")
        )
        completed_days = sum(1 for item in workouts if item.completed)
        hard_days = sum(1 for item in workouts if (item.perceived_exertion or 0) >= 8)
        recovery_days = sum(
            1
            for item in recommendations
            if item.recommendation_type
            in (
                TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY,
                TrainingRecommendation.RecommendationType.CARDIO_LIGHT,
                TrainingRecommendation.RecommendationType.FULL_REST,
            )
        )
        return {
            "completed_days": completed_days,
            "hard_days": hard_days,
            "recovery_days": recovery_days,
            "workouts_count": len(workouts),
            "recommendations_count": len(recommendations),
        }
