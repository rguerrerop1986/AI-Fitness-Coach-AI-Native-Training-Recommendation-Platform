"""
Read-only queries for training history. Used by services to avoid ORM details in business logic.
"""
from datetime import date, timedelta
from typing import Optional

from django.db.models import QuerySet

from .models import DailyCheckIn, TrainingRecommendation, WorkoutLog


def get_recent_workout_logs(
    user,
    days: int = 14,
    before_date: Optional[date] = None,
) -> QuerySet[WorkoutLog]:
    """
    Last N days of workout logs for the user, ordered by date descending.
    before_date: exclusive upper bound (e.g. today + 1 to include today).
    """
    end = before_date or date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    return (
        WorkoutLog.objects.filter(user=user, date__gte=start, date__lt=end)
        .select_related('video')
        .order_by('-date')
    )


def get_checkin_for_date(user, for_date: date) -> Optional[DailyCheckIn]:
    """Return the DailyCheckIn for the user on the given date, or None."""
    return DailyCheckIn.objects.filter(user=user, date=for_date).first()


def get_recent_checkins(user, days: int = 14, before_date: Optional[date] = None):
    """Last N days of daily check-ins for the user, ordered by date descending."""
    end = before_date or date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    return (
        DailyCheckIn.objects.filter(user=user, date__gte=start, date__lt=end)
        .order_by('-date')
    )


def get_recent_recommendations(user, days: int = 14, before_date: Optional[date] = None):
    """Last N days of training recommendations for the user, ordered by date descending."""
    end = before_date or date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    return (
        TrainingRecommendation.objects.filter(user=user, date__gte=start, date__lt=end)
        .select_related('recommended_exercise', 'recommended_video')
        .order_by('-date')
    )


def get_recent_feedbacks(user, days: int = 14, before_date: Optional[date] = None):
    """
    Recent workout logs as feedback source (no separate feedback table).
    WorkoutLog contains: completed, rpe, satisfaction, performance, pain_during_workout,
    recovery_fast, body_feedback, emotional_feedback. Ordered by date descending.
    """
    return get_recent_workout_logs(user, days=days, before_date=before_date)
