"""Unit tests for closed-loop progression V1.1 (evaluate_outcome, apply_progression_update)."""
from datetime import date
from django.test import TestCase

from apps.clients.models import Client
from apps.tracking.models import TrainingLog, ClientProgressionState
from apps.catalogs.models import Exercise
from apps.recommendations.services.progression import (
    evaluate_outcome,
    apply_progression_update,
    get_or_create_progression_state,
    tick_cooldown_by_day,
    OutcomeResult,
)


class ProgressionEvaluateOutcomeTest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='prog@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=70,
            level='beginner',
        )
        self.exercise = Exercise.objects.create(
            name='Test exercise',
            muscle_group='quads',
            difficulty='beginner',
            intensity=5,
            instructions='Do it.',
        )

    def _log(self, rpe=None, energy_level=None, pain_level=None):
        return TrainingLog.objects.create(
            client=self.client_obj,
            date=date.today(),
            suggested_exercise=self.exercise,
            executed_exercise=self.exercise,
            execution_status=TrainingLog.ExecutionStatus.DONE,
            rpe=rpe,
            energy_level=energy_level,
            pain_level=pain_level,
        )

    def test_pain_7_injury_risk_score_minus2(self):
        log = self._log(rpe=5, energy_level=6, pain_level=7)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, -2)
        self.assertIn('injury_risk', result.flags)

    def test_pain_4_to_6_pain_attention_score_minus1(self):
        log = self._log(rpe=5, energy_level=5, pain_level=5)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, -1)
        self.assertIn('pain_attention', result.flags)

    def test_rpe_9_overreached_score_minus2(self):
        log = self._log(rpe=9, energy_level=4, pain_level=2)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, -2)
        self.assertIn('overreached', result.flags)

    def test_rpe_8_too_hard_score_minus1(self):
        log = self._log(rpe=8, energy_level=5, pain_level=1)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, -1)
        self.assertIn('too_hard', result.flags)

    def test_energy_low_score_minus1(self):
        log = self._log(rpe=4, energy_level=2, pain_level=0)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, -1)
        self.assertIn('low_energy', result.flags)

    def test_underloaded_ready_score_plus2(self):
        log = self._log(rpe=3, energy_level=8, pain_level=1)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, 2)
        self.assertIn('underloaded_ready', result.flags)

    def test_good_adaptation_score_plus1(self):
        log = self._log(rpe=5, energy_level=7, pain_level=2)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, 1)
        self.assertIn('good_adaptation', result.flags)

    def test_neutral_score_zero(self):
        log = self._log(rpe=6, energy_level=5, pain_level=3)
        result = evaluate_outcome(log)
        self.assertEqual(result.outcome_score, 0)
        self.assertIn('neutral', result.flags)


class ProgressionApplyUpdateTest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='apply@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=70,
            level='beginner',
        )
        self.state = get_or_create_progression_state(self.client_obj)

    def test_load_score_clamp(self):
        self.state.current_load_score = 9.0
        self.state.save()
        outcome = OutcomeResult(outcome_score=5, flags=['underloaded_ready'])
        state, delta, msg = apply_progression_update(self.state, outcome)
        self.assertEqual(state.current_load_score, 10.0)
        self.assertIn('Buen trabajo', msg)

    def test_injury_risk_cooldown(self):
        self.state.intensity_bias = 1
        self.state.save()
        today = date(2026, 2, 1)
        outcome = OutcomeResult(outcome_score=-2, flags=['injury_risk'])
        state, delta, msg = apply_progression_update(self.state, outcome, log_date=today)
        self.assertEqual(state.intensity_bias, -2)
        self.assertEqual(state.cooldown_days_remaining, 3)
        self.assertEqual(state.cooldown_last_tick_date, today)
        self.assertIn('Dolor alto', msg)

    def test_intensity_bias_increases_when_load_high(self):
        self.state.current_load_score = 3.5
        self.state.intensity_bias = 0
        self.state.save()
        outcome = OutcomeResult(outcome_score=1, flags=['good_adaptation'])
        state, delta, msg = apply_progression_update(self.state, outcome)
        self.assertEqual(state.intensity_bias, 1)

    def test_intensity_bias_decreases_when_load_low(self):
        self.state.current_load_score = -3.5
        self.state.intensity_bias = 0
        self.state.save()
        outcome = OutcomeResult(outcome_score=-1, flags=['too_hard'])
        state, delta, msg = apply_progression_update(self.state, outcome)
        self.assertEqual(state.intensity_bias, -1)


class TickCooldownByDayTest(TestCase):
    """Cooldown ticks by calendar day (on GET/generate), not per session."""

    def setUp(self):
        self.client_obj = Client.objects.create(
            first_name='Tick',
            last_name='Client',
            email='tick@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=70,
            level='beginner',
        )
        self.state = get_or_create_progression_state(self.client_obj)

    def test_tick_two_days_elapsed_remaining_becomes_one(self):
        """cooldown_days_remaining=3, last_tick=2026-02-01, today=2026-02-03 => remaining=1."""
        self.state.cooldown_days_remaining = 3
        self.state.cooldown_last_tick_date = date(2026, 2, 1)
        self.state.intensity_bias = -2
        self.state.save()
        tick_cooldown_by_day(self.state, date(2026, 2, 3))
        self.state.refresh_from_db()
        self.assertEqual(self.state.cooldown_days_remaining, 1)
        self.assertEqual(self.state.cooldown_last_tick_date, date(2026, 2, 3))

    def test_tick_remaining_never_below_zero(self):
        """remaining=1, last_tick=2026-02-01, today=2026-02-05 => remaining=0 (not negative)."""
        self.state.cooldown_days_remaining = 1
        self.state.cooldown_last_tick_date = date(2026, 2, 1)
        self.state.intensity_bias = -2
        self.state.save()
        tick_cooldown_by_day(self.state, date(2026, 2, 5))
        self.state.refresh_from_db()
        self.assertEqual(self.state.cooldown_days_remaining, 0)
        self.assertEqual(self.state.intensity_bias, 0)

    def test_tick_first_time_sets_last_tick_no_decrement(self):
        """last_tick=None, remaining=3: first tick sets last_tick=today, remaining stays 3."""
        self.state.cooldown_days_remaining = 3
        self.state.cooldown_last_tick_date = None
        self.state.save()
        tick_cooldown_by_day(self.state, date(2026, 2, 1))
        self.state.refresh_from_db()
        self.assertEqual(self.state.cooldown_days_remaining, 3)
        self.assertEqual(self.state.cooldown_last_tick_date, date(2026, 2, 1))

    def test_tick_next_day_decrements_one(self):
        """After first tick, next day decrements by 1."""
        self.state.cooldown_days_remaining = 3
        self.state.cooldown_last_tick_date = date(2026, 2, 1)
        self.state.save()
        tick_cooldown_by_day(self.state, date(2026, 2, 2))
        self.state.refresh_from_db()
        self.assertEqual(self.state.cooldown_days_remaining, 2)
        self.assertEqual(self.state.cooldown_last_tick_date, date(2026, 2, 2))
