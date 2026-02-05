"""
Selectors for recommendation engine: read-only queries for plan cycles and training history.
Keeps service layer free of ORM details and eases testing.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db.models import Q, QuerySet

from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise


def get_active_plan_cycle_for_client(client: Client, for_date: date) -> Optional[PlanCycle]:
    """
    Return the ACTIVE PlanCycle that covers for_date for this client, or None.
    Only one active cycle per client at a time (enforced by PlanCycle.clean).
    """
    return PlanCycle.objects.filter(
        client=client,
        status=PlanCycle.Status.ACTIVE,
        start_date__lte=for_date,
        end_date__gte=for_date,
    ).first()


def get_recent_training_logs(
    client: Client,
    days: int = 14,
    before_date: Optional[date] = None,
) -> QuerySet[TrainingLog]:
    """
    Last N days of training logs for the client, ordered by date desc.
    before_date: exclusive upper bound (default: tomorrow so "today" is included).
    """
    end = before_date or date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    return (
        TrainingLog.objects.filter(client=client, date__gte=start, date__lt=end)
        .select_related('suggested_exercise', 'executed_exercise')
        .order_by('-date')
    )


def compute_pain_trend(logs: list[TrainingLog]) -> Optional[str]:
    """
    Simple trend: 'high' if last log pain >= 6, 'rising' if previous had lower pain, else 'stable/low'.
    """
    if not logs:
        return None
    last = logs[0]
    prev = logs[1] if len(logs) > 1 else None
    last_pain = last.pain_level if last else None
    if last_pain is None:
        return 'unknown'
    if last_pain >= 6:
        if prev and (prev.pain_level or 0) < 6:
            return 'rising'
        return 'high'
    return 'stable'


def compute_adherence_rate(logs: list[TrainingLog], window_days: int = 14) -> float:
    """
    Fraction of logs in the window that are DONE or PARTIAL (completed in some form).
    Returns 0.0 if no logs.
    """
    completed_statuses = {TrainingLog.ExecutionStatus.DONE, TrainingLog.ExecutionStatus.PARTIAL}
    completed = sum(1 for log in logs if log.execution_status in completed_statuses)
    total = len(logs)
    if total == 0:
        return 0.0
    return round(completed / total, 2)


def get_exercises_for_recommendation(
    *,
    max_intensity: Optional[int] = None,
    tags_any: Optional[list[str]] = None,
    exclude_exercise_ids: Optional[list[int]] = None,
) -> QuerySet[Exercise]:
    """
    Base queryset of active exercises, optionally filtered by intensity and tags.
    tags_any: exercise must have at least one of these tags (JSON array contains).
    """
    qs = Exercise.objects.filter(is_active=True)
    if max_intensity is not None:
        qs = qs.filter(intensity__lte=max_intensity)
    if tags_any:
        tag_filter = Q()
        for tag in tags_any:
            tag_filter |= Q(tags__contains=[tag])
        qs = qs.filter(tag_filter)
    if exclude_exercise_ids:
        qs = qs.exclude(id__in=exclude_exercise_ids)
    return qs.order_by('?')  # Randomize among candidates for variety


def get_last_log(logs: list[TrainingLog]) -> Optional[TrainingLog]:
    """First log in list (logs are ordered by date desc)."""
    return logs[0] if logs else None
