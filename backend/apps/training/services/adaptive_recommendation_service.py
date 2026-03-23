"""Adaptive daily recommendation engine orchestrating readiness + policy rules."""

from __future__ import annotations

from datetime import date

from django.db import transaction

from apps.training.models import DailyCheckIn, TrainingRecommendation
from apps.training.services.coach_message_service import CoachMessageService
from apps.training.services.history_service import HistoryService
from apps.training.services.readiness_service import ReadinessService
from apps.training.services.training_selector import TrainingSelector


class AdaptiveRecommendationService:
    """Production rule engine for daily coaching recommendation."""

    def __init__(self) -> None:
        self.readiness_service = ReadinessService()
        self.message_service = CoachMessageService()
        self.selector = TrainingSelector()
        self.history_service = HistoryService()

    def generate_for_date(self, user, target_date: date, regenerate: bool = True) -> tuple[TrainingRecommendation, bool]:
        checkin = DailyCheckIn.objects.filter(user=user, date=target_date).first()
        if not checkin:
            raise ValueError("Daily check-in is required before generating recommendation.")

        if not regenerate:
            existing = TrainingRecommendation.objects.filter(user=user, date=target_date).first()
            if existing:
                return existing, False

        readiness = self.readiness_service.analyze(checkin)
        history = self.history_service.get_recent_summary(user.id, target_date)
        recommendation_type = self._choose_recommendation_type(checkin, readiness.readiness_score)
        selection = self.selector.select(recommendation_type)

        warning_codes = readiness.warnings[:]
        high_motivation_poor_recovery = (
            (checkin.motivation_level or 0) >= 8
            and ((checkin.sleep_quality or 10) <= 4 or (checkin.muscle_soreness or 0) >= 8)
        )
        if high_motivation_poor_recovery:
            warning_codes.append("high_motivation_poor_recovery")

        message = self.message_service.build_message(
            recommendation_type=recommendation_type,
            readiness_band=readiness.readiness_band,
            warnings=warning_codes,
            checkin_flags={
                "injury": bool(checkin.feels_pain_or_injury),
                "high_motivation_poor_recovery": high_motivation_poor_recovery,
            },
        )
        reasoning_summary = (
            f"Readiness {readiness.readiness_score}/100 ({readiness.readiness_band}). "
            f"History: {history['completed_days']} completed days, {history['hard_days']} hard days in last 7."
        )

        with transaction.atomic():
            recommendation, _ = TrainingRecommendation.objects.update_or_create(
                user=user,
                date=target_date,
                defaults={
                    "checkin": checkin,
                    "recommendation_type": recommendation_type,
                    "readiness_score": readiness.readiness_score,
                    "reasoning_summary": reasoning_summary,
                    "coach_message": message,
                    "warnings": warning_codes,
                    "intensity_level": selection.intensity_level,
                    "duration_minutes": selection.duration_minutes,
                    "recommended_video_id": selection.recommended_video_id,
                    "metadata": {
                        "readiness": readiness.asdict(),
                        "history": history,
                    },
                    "rule_based_payload": {
                        "readiness_band": readiness.readiness_band,
                        "warning_codes": warning_codes,
                    },
                },
            )
        return recommendation, True

    def _choose_recommendation_type(self, checkin: DailyCheckIn, readiness_score: float) -> str:
        # Case 4: pain/injury/very low recovery
        if checkin.feels_pain_or_injury or (checkin.muscle_soreness or 0) >= 9 or readiness_score < 30:
            return TrainingRecommendation.RecommendationType.FULL_REST

        # Case 5 edge: high motivation but poor recovery -> prudent option
        if (checkin.motivation_level or 0) >= 8 and (
            (checkin.sleep_quality or 10) <= 4 or (checkin.muscle_soreness or 0) >= 8
        ):
            return TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY

        # Case 3
        if (checkin.sleep_quality or 10) <= 5 or (checkin.stress_level or 1) >= 8:
            return TrainingRecommendation.RecommendationType.CARDIO_LIGHT

        # Case 1
        if (
            readiness_score >= 85
            and (checkin.muscle_soreness or 0) <= 6
            and (checkin.stress_level or 0) <= 5
            and not checkin.feels_pain_or_injury
        ):
            if checkin.wants_strength_today:
                return TrainingRecommendation.RecommendationType.STRENGTH_UPPER
            return TrainingRecommendation.RecommendationType.INSANITY_MAX

        # Case 2
        if 70 <= readiness_score <= 84:
            if checkin.wants_strength_today:
                return TrainingRecommendation.RecommendationType.STRENGTH_LOWER
            if checkin.wants_recovery_today:
                return TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY
            return TrainingRecommendation.RecommendationType.INSANITY_MODERATE

        if checkin.wants_recovery_today:
            return TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY
        return TrainingRecommendation.RecommendationType.HYBRID_TRAINING
