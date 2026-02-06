"""
Closed-loop learning V1.1: evaluate post-workout outcome and apply progression updates.
Heuristic-based (no ML). State persisted in ClientProgressionState.
"""
from dataclasses import dataclass
from typing import Any, Optional

from apps.tracking.models import TrainingLog, ClientProgressionState
from apps.clients.models import Client


@dataclass
class OutcomeResult:
    """Result of evaluating a training log outcome."""
    outcome_score: int  # -2 to +2
    flags: list[str]


def evaluate_outcome(log: TrainingLog) -> OutcomeResult:
    """
    Evaluate post-workout outcome from RPE, energy, pain.
    Returns outcome_score (-2..+2) and flags for audit.
    Priority: injury/overreach first, then negative, then positive.
    """
    rpe = log.rpe if log.rpe is not None else 0
    energy = log.energy_level if log.energy_level is not None else 10
    pain = log.pain_level if log.pain_level is not None else 0

    # Worst first: injury risk
    if pain >= 7:
        return OutcomeResult(outcome_score=-2, flags=['injury_risk'])
    if rpe >= 9:
        return OutcomeResult(outcome_score=-2, flags=['overreached'])
    if pain >= 4:
        return OutcomeResult(outcome_score=-1, flags=['pain_attention'])
    if rpe >= 8:
        return OutcomeResult(outcome_score=-1, flags=['too_hard'])
    if energy <= 3:
        return OutcomeResult(outcome_score=-1, flags=['low_energy'])
    # Positive
    if 5 <= rpe <= 6 and energy >= 6 and pain <= 3:
        return OutcomeResult(outcome_score=1, flags=['good_adaptation'])
    if rpe <= 4 and energy >= 7 and pain <= 2:
        return OutcomeResult(outcome_score=2, flags=['underloaded_ready'])
    return OutcomeResult(outcome_score=0, flags=['neutral'])


def apply_progression_update(
    state: ClientProgressionState,
    outcome: OutcomeResult,
) -> tuple[ClientProgressionState, dict[str, Any], str]:
    """
    Apply outcome to progression state. Returns (updated_state, delta, user_message).
    delta: intensity_bias_before, intensity_bias_after, outcome_score, flags.
    """
    delta: dict[str, Any] = {
        'outcome_score': outcome.outcome_score,
        'flags': outcome.flags,
        'intensity_bias_before': state.intensity_bias,
        'current_load_score_before': state.current_load_score,
    }
    bias_before = state.intensity_bias

    # Clamp load score -10..+10
    state.current_load_score = max(-10.0, min(10.0, state.current_load_score + outcome.outcome_score))
    delta['current_load_score_after'] = state.current_load_score

    # Injury risk: force low intensity for 3 days
    if 'injury_risk' in outcome.flags:
        state.intensity_bias = -2
        state.cooldown_days_remaining = 3
        state.high_days_streak = 0
        state.save(update_fields=['current_load_score', 'intensity_bias', 'cooldown_days_remaining', 'high_days_streak', 'updated_at'])
        delta['intensity_bias_after'] = state.intensity_bias
        return state, delta, 'Dolor alto: mañana será recuperación / bajo impacto. Si persiste, consulta a tu médico.'

    # Cooldown: decrement if not injury_risk this time
    if state.cooldown_days_remaining > 0:
        state.cooldown_days_remaining -= 1
        if state.cooldown_days_remaining == 0 and state.intensity_bias == -2:
            state.intensity_bias = 0  # reset after cooldown

    # Adjust intensity_bias from load score (when not in cooldown)
    if state.cooldown_days_remaining == 0:
        if state.current_load_score >= 3 and state.intensity_bias < 2:
            state.intensity_bias = min(2, state.intensity_bias + 1)
        elif state.current_load_score <= -3 and state.intensity_bias > -2:
            state.intensity_bias = max(-2, state.intensity_bias - 1)

    # Streaks: if we had a high day and outcome was negative, we're not counting streak here
    # (streak is updated in daily_exercise when we *recommend* HIGH). Here we only reset if needed.
    if outcome.outcome_score < 0:
        state.high_days_streak = 0

    state.save(update_fields=['current_load_score', 'intensity_bias', 'cooldown_days_remaining', 'high_days_streak', 'updated_at'])
    delta['intensity_bias_after'] = state.intensity_bias

    # User-facing message
    if outcome.outcome_score >= 1:
        message = 'Buen trabajo: mañana subiremos un poco la intensidad.'
    elif outcome.outcome_score <= -1:
        message = 'Mañana priorizamos recuperación o sesión más suave.'
    else:
        message = 'Todo en orden. Seguimos con el mismo ritmo.'

    return state, delta, message


def get_or_create_progression_state(client: Client) -> ClientProgressionState:
    """Get existing ClientProgressionState or create one with defaults."""
    state, _ = ClientProgressionState.objects.get_or_create(
        client=client,
        defaults={
            'current_load_score': 0.0,
            'intensity_bias': 0,
            'preferred_types': {},
            'high_days_streak': 0,
            'cooldown_days_remaining': 0,
        },
    )
    return state
