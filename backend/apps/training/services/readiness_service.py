"""Daily readiness scoring engine with explicit penalties and bonuses."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Any

from apps.training.models import CompletedWorkout, DailyCheckIn, TrainingRecommendation


@dataclass(frozen=True)
class ScoreAdjustment:
    code: str
    value: float


@dataclass(frozen=True)
class ReadinessAnalysis:
    readiness_score: float
    base_score: float
    penalties: list[ScoreAdjustment]
    bonuses: list[ScoreAdjustment]
    warnings: list[str]
    readiness_band: str

    def asdict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["penalties"] = [asdict(item) for item in self.penalties]
        payload["bonuses"] = [asdict(item) for item in self.bonuses]
        return payload


class ReadinessService:
    """Computes a 0-100 readiness score with auditable breakdown."""

    WEIGHTS: dict[str, float] = {
        "sleep_quality": 0.18,
        "energy_level": 0.18,
        "motivation_level": 0.10,
        "diet_adherence_yesterday": 0.10,
        "hydration_level": 0.08,
        "recovery_feeling": 0.12,
        "mental_clarity": 0.08,
        "workout_desire": 0.06,
        "stress_level": -0.05,
        "muscle_soreness": -0.05,
    }

    def analyze(self, checkin: DailyCheckIn) -> ReadinessAnalysis:
        base_score = self._compute_base_score(checkin)
        penalties = self._compute_penalties(checkin)
        bonuses = self._compute_bonuses(checkin)
        total_adjustment = sum(item.value for item in penalties + bonuses)
        readiness_score = max(0.0, min(100.0, round(base_score + total_adjustment, 1)))
        warnings = [item.code for item in penalties]
        return ReadinessAnalysis(
            readiness_score=readiness_score,
            base_score=round(base_score, 1),
            penalties=penalties,
            bonuses=bonuses,
            warnings=warnings,
            readiness_band=self._readiness_band(readiness_score),
        )

    def _score_1_to_10(self, value: int | None) -> float:
        if value is None:
            return 5.0
        return float(max(1, min(10, value)))

    def _compute_base_score(self, checkin: DailyCheckIn) -> float:
        weighted = 0.0
        for field, weight in self.WEIGHTS.items():
            val = self._score_1_to_10(getattr(checkin, field, None))
            if weight < 0:
                # Stress/soreness are inverse signals: lower is better.
                weighted += ((11.0 - val) / 10.0) * abs(weight)
            else:
                weighted += (val / 10.0) * weight
        return weighted * 100.0

    def _compute_penalties(self, checkin: DailyCheckIn) -> list[ScoreAdjustment]:
        penalties: list[ScoreAdjustment] = []
        if checkin.had_alcohol_yesterday:
            penalties.append(ScoreAdjustment("alcohol_yesterday", -8))
        if checkin.feels_pain_or_injury:
            penalties.append(ScoreAdjustment("pain_or_injury", -20))
        if (checkin.sleep_quality or 10) <= 4:
            penalties.append(ScoreAdjustment("sleep_very_low", -12))
        if (checkin.stress_level or 1) >= 8:
            penalties.append(ScoreAdjustment("stress_high", -10))

        if self._has_consecutive_high_intensity_days(checkin.user_id, checkin.date, 2):
            penalties.append(ScoreAdjustment("two_consecutive_high_intensity_days", -10))
        if self._has_consecutive_hard_days(checkin.user_id, checkin.date, 3):
            penalties.append(ScoreAdjustment("three_consecutive_hard_days", -15))

        return penalties

    def _compute_bonuses(self, checkin: DailyCheckIn) -> list[ScoreAdjustment]:
        bonuses: list[ScoreAdjustment] = []
        if self._has_recent_recovery_supportive_days(checkin.user_id, checkin.date, 2):
            bonuses.append(ScoreAdjustment("recent_recovery_supportive_days", 6))
        if self._has_good_nutrition_streak(checkin.user_id, checkin.date):
            bonuses.append(ScoreAdjustment("nutrition_streak_good", 5))
        if self._has_good_recent_consistency(checkin.user_id, checkin.date):
            bonuses.append(ScoreAdjustment("recent_consistency_good", 5))
        return bonuses

    def _history_window(self, target_date: date, days: int = 7) -> tuple[date, date]:
        return (target_date - timedelta(days=days), target_date - timedelta(days=1))

    def _recent_recommendations(self, user_id: int, target_date: date) -> list[TrainingRecommendation]:
        start, end = self._history_window(target_date)
        return list(
            TrainingRecommendation.objects.filter(user_id=user_id, date__range=(start, end)).order_by("-date")
        )

    def _recent_completed_workouts(self, user_id: int, target_date: date) -> list[CompletedWorkout]:
        start, end = self._history_window(target_date)
        return list(
            CompletedWorkout.objects.filter(user_id=user_id, date__range=(start, end), completed=True).order_by("-date")
        )

    def _has_consecutive_high_intensity_days(self, user_id: int, target_date: date, streak_days: int) -> bool:
        recs = self._recent_recommendations(user_id, target_date)
        if len(recs) < streak_days:
            return False
        last = recs[:streak_days]
        return all(
            rec.intensity_level in (
                TrainingRecommendation.IntensityLevel.HIGH,
                TrainingRecommendation.IntensityLevel.MODERATE,
            )
            and rec.recommendation_type in (
                TrainingRecommendation.RecommendationType.INSANITY_MAX,
                TrainingRecommendation.RecommendationType.INSANITY_MODERATE,
                TrainingRecommendation.RecommendationType.HYBRID_TRAINING,
            )
            for rec in last
        )

    def _has_consecutive_hard_days(self, user_id: int, target_date: date, streak_days: int) -> bool:
        workouts = self._recent_completed_workouts(user_id, target_date)
        if len(workouts) < streak_days:
            return False
        return all((item.perceived_exertion or 0) >= 8 for item in workouts[:streak_days])

    def _has_recent_recovery_supportive_days(self, user_id: int, target_date: date, min_days: int) -> bool:
        recs = self._recent_recommendations(user_id, target_date)
        supportive = {
            TrainingRecommendation.RecommendationType.FULL_REST,
            TrainingRecommendation.RecommendationType.MOBILITY_RECOVERY,
            TrainingRecommendation.RecommendationType.CARDIO_LIGHT,
            TrainingRecommendation.RecommendationType.REST_DAY,
            TrainingRecommendation.RecommendationType.RECOVERY,
        }
        return sum(1 for rec in recs if rec.recommendation_type in supportive) >= min_days

    def _has_good_nutrition_streak(self, user_id: int, target_date: date) -> bool:
        start, end = self._history_window(target_date)
        return (
            DailyCheckIn.objects.filter(
                user_id=user_id,
                date__range=(start, end),
                diet_adherence_yesterday__gte=7,
            ).count()
            >= 3
        )

    def _has_good_recent_consistency(self, user_id: int, target_date: date) -> bool:
        completed = self._recent_completed_workouts(user_id, target_date)
        return len(completed) >= 4

    def _readiness_band(self, score: float) -> str:
        if score >= 85:
            return "high"
        if score >= 70:
            return "good"
        if score >= 50:
            return "moderate"
        if score >= 30:
            return "low"
        return "recovery_only"
