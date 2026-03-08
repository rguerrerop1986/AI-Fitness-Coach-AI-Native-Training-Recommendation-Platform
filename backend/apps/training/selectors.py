"""
Read-only queries for training history. Used by services to avoid ORM details in business logic.
"""
from datetime import date, timedelta
from typing import Optional

from django.db.models import QuerySet

from .models import DailyCheckIn, WorkoutLog


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
