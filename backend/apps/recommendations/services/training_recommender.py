"""
Rule-based training recommender (rules_v1).
Suggests one exercise for a client for a given date using recent TrainingLog feedback.
ML-ready: output includes meta and confidence for future model replacement.
"""
from datetime import date
from decimal import Decimal
from typing import Any

from apps.clients.models import Client
from apps.catalogs.models import Exercise
from apps.tracking.models import TrainingLog

from apps.recommendations.selectors import (
    get_active_plan_cycle_for_client,
    get_recent_training_logs,
    compute_pain_trend,
    compute_adherence_rate,
    get_exercises_for_recommendation,
    get_last_log,
)

VERSION = 'rules_v1'

# Rule identifiers for meta.applied_rule
RULE_PAIN_REDUCE = 'pain_high_mobility_low_impact'
RULE_ENERGY_LOW = 'energy_low_reduce_intensity'
RULE_NOT_DONE_STREAK = 'not_done_streak_reduce_and_vary'
RULE_PROGRESS_OK = 'progress_ok_increase_intensity'
RULE_DEFAULT = 'default_balanced'


def suggest_exercise_for_today(client: Client, for_date: date) -> dict[str, Any]:
    """
    Suggest one exercise for the client for the given date.
    Returns: { exercise, rationale, meta, confidence }
    - exercise: Exercise instance or None if no suggestion (e.g. no active plan)
    - rationale: human-readable explanation (always set)
    - meta: dict with pain_trend, adherence_rate, applied_rule, and optional details
    - confidence: float 0–1
    """
    meta: dict[str, Any] = {}
    rationale_parts: list[str] = []

    # 1) Active PlanCycle covering for_date
    plan_cycle = get_active_plan_cycle_for_client(client, for_date)
    if not plan_cycle:
        return {
            'exercise': None,
            'rationale': 'No tienes un plan activo para esta fecha. Activa un plan con tu coach.',
            'meta': {'applied_rule': 'no_active_plan'},
            'confidence': Decimal('0'),
        }

    # 2) Last 14 TrainingLogs (before for_date)
    logs = list(
        get_recent_training_logs(client, days=14, before_date=for_date)
    )
    meta['pain_trend'] = compute_pain_trend(logs)
    meta['adherence_rate'] = compute_adherence_rate(logs)
    last_log = get_last_log(logs)

    # Build candidate filters and rationale from rules (order matters: safety first)
    max_intensity: int | None = None
    tags_any: list[str] | None = None
    applied_rule = RULE_DEFAULT

    # 3) If last log pain_level >= 6 -> mobility or low_impact
    if last_log is not None and last_log.pain_level is not None and last_log.pain_level >= 6:
        tags_any = ['mobility', 'low_impact']
        applied_rule = RULE_PAIN_REDUCE
        rationale_parts.append(
            'Reportaste dolor elevado recientemente; te sugerimos movilidad o bajo impacto.'
        )

    # 4) If last log energy_level <= 3 -> intensity <= 4
    if last_log is not None and last_log.energy_level is not None and last_log.energy_level <= 3:
        if max_intensity is None or max_intensity > 4:
            max_intensity = 4
        if applied_rule == RULE_DEFAULT:
            applied_rule = RULE_ENERGY_LOW
        if not rationale_parts:
            rationale_parts.append(
                'Tu nivel de energía fue bajo; elegimos una sesión suave.'
            )

    # 5) Last 2 days NOT_DONE -> lower intensity and vary type
    recent_two = logs[:2] if len(logs) >= 2 else logs
    not_done_count = sum(
        1 for log in recent_two
        if log.execution_status == TrainingLog.ExecutionStatus.NOT_DONE
    )
    if not_done_count >= 2:
        if max_intensity is None or max_intensity > 4:
            max_intensity = 4
        applied_rule = RULE_NOT_DONE_STREAK
        rationale_parts.append(
            'Llevas dos días sin entrenar; proponemos algo más accesible para retomar.'
        )

    # 6) Last 3 DONE with rpe <= 6 -> increase intensity gradually (+1)
    recent_three = logs[:3] if len(logs) >= 3 else logs
    done_with_low_rpe = all(
        log.execution_status == TrainingLog.ExecutionStatus.DONE and (log.rpe or 10) <= 6
        for log in recent_three
    )
    if done_with_low_rpe and not rationale_parts and not tags_any:
        # We don't have a "current" intensity on the client; we use exercise pool.
        # So we prefer exercises with intensity >= 6 when progress is OK.
        applied_rule = RULE_PROGRESS_OK
        rationale_parts.append(
            'Vas bien con las sesiones recientes; hoy podemos subir un poco la intensidad.'
        )
        # Filter to exercises with intensity >= 6 (we'll do min_intensity in selector if needed)
        # get_exercises_for_recommendation only has max_intensity; so we don't set max_intensity
        # and allow higher intensity exercises. So we leave max_intensity as None here.
        pass

    meta['applied_rule'] = applied_rule

    # Default rationale if nothing else
    if not rationale_parts:
        rationale_parts.append(
            'Rutina equilibrada según tu plan y tu historial reciente.'
        )

    # Pick exercise: apply filters
    qs = get_exercises_for_recommendation(
        max_intensity=max_intensity,
        tags_any=tags_any,
    )
    # For RULE_PROGRESS_OK prefer higher intensity (e.g. intensity >= 6)
    if applied_rule == RULE_PROGRESS_OK:
        qs = qs.filter(intensity__gte=6)

    exercise = qs.first()
    if not exercise:
        # Fallback: any active exercise with optional intensity cap
        qs = get_exercises_for_recommendation(max_intensity=max_intensity)
        exercise = qs.first()

    if not exercise:
        return {
            'exercise': None,
            'rationale': ' '.join(rationale_parts) + ' No hay ejercicios en el catálogo que cumplan los criterios.',
            'meta': meta,
            'confidence': Decimal('0.3'),
        }

    # Confidence: higher when we have recent data and applied a clear rule
    confidence = Decimal('0.7')
    if len(logs) >= 7:
        confidence = Decimal('0.85')
    if applied_rule != RULE_DEFAULT:
        confidence = min(Decimal('0.95'), confidence + Decimal('0.05'))

    return {
        'exercise': exercise,
        'rationale': ' '.join(rationale_parts),
        'meta': meta,
        'confidence': confidence,
    }
