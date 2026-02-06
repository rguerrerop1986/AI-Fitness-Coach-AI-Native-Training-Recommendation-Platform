"""Unit tests for daily exercise recommendation V1 (heuristic engine) and V1.1 (progression)."""
from datetime import date, timedelta
from django.test import TestCase
from apps.clients.models import Client
from apps.tracking.models import TrainingLog, DailyExerciseRecommendation, ClientProgressionState
from apps.catalogs.models import Exercise
from django.contrib.auth import get_user_model
from apps.recommendations.services.daily_exercise import generate_daily_recommendation
from apps.recommendations.services.progression import get_or_create_progression_state

User = get_user_model()


class DailyExerciseRecommendationTest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='dailyex@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=70,
            level='beginner',
        )
        self.mobility = Exercise.objects.create(
            name='Movilidad test',
            muscle_group='other',
            difficulty='beginner',
            intensity=2,
            tags=['mobility', 'low_impact'],
            instructions='Movilidad suave.',
        )
        self.strength = Exercise.objects.create(
            name='Fuerza básica',
            muscle_group='quads',
            difficulty='beginner',
            intensity=5,
            tags=['strength'],
            instructions='Sentadillas.',
        )

    def test_cold_start_creates_recommendation(self):
        """Without any logs, generates a recommendation by level."""
        rec = generate_daily_recommendation(self.client_obj, date.today())
        self.assertIsNotNone(rec.id)
        self.assertEqual(rec.client_id, self.client_obj.id)
        self.assertEqual(rec.date, date.today())
        self.assertEqual(rec.status, DailyExerciseRecommendation.Status.RECOMMENDED)
        self.assertGreater(len(rec.rationale or ''), 0)
        self.assertIsNotNone(rec.exercise_id or rec.rationale)

    def test_same_day_returns_existing(self):
        """Second call for same client/date returns same record."""
        rec1 = generate_daily_recommendation(self.client_obj, date.today())
        rec2 = generate_daily_recommendation(self.client_obj, date.today())
        self.assertEqual(rec1.id, rec2.id)

    def test_high_pain_recommends_mobility_or_low_impact(self):
        """When last log has pain >= 7, rationale and metadata reflect safety rule."""
        TrainingLog.objects.create(
            client=self.client_obj,
            date=date.today() - timedelta(days=1),
            execution_status=TrainingLog.ExecutionStatus.DONE,
            pain_level=7,
            energy_level=5,
        )
        rec = generate_daily_recommendation(self.client_obj, date.today())
        self.assertIn('pain_high_mobility', rec.metadata.get('applied_rules', []))
        self.assertIn('dolor', (rec.rationale or '').lower() or 'movilidad')

    def test_progression_state_used_intensity_target(self):
        """V1.1: metadata includes progression_state_snapshot_before and intensity_target_used."""
        state = get_or_create_progression_state(self.client_obj)
        state.intensity_bias = -1
        state.save()
        rec = generate_daily_recommendation(self.client_obj, date.today())
        self.assertIn('progression_state_snapshot_before', rec.metadata)
        self.assertIn('intensity_target_used', rec.metadata)
        self.assertEqual(rec.metadata['intensity_target_used'], 3)  # beginner 4 + (-1) = 3

    def test_guardrail_max_2_high_days(self):
        """When high_days_streak >= 2, next recommendation is not HIGH."""
        state = get_or_create_progression_state(self.client_obj)
        state.high_days_streak = 2
        state.last_recommended_type = 'strength'
        state.save()
        rec = generate_daily_recommendation(self.client_obj, date.today())
        self.assertIn('guardrail_max_2_high_days', rec.metadata.get('applied_rules', []))
        self.assertNotEqual(rec.intensity, DailyExerciseRecommendation.Intensity.HIGH)

    def test_during_cooldown_no_high_recommendation(self):
        """When cooldown_days_remaining > 0 (injury_risk), generate_daily_recommendation does not recommend HIGH."""
        state = get_or_create_progression_state(self.client_obj)
        state.cooldown_days_remaining = 2
        state.cooldown_last_tick_date = date.today()  # already ticked today
        state.intensity_bias = -2
        state.save()
        rec = generate_daily_recommendation(self.client_obj, date.today())
        self.assertIn('cooldown_after_injury', rec.metadata.get('applied_rules', []))
        self.assertNotEqual(rec.intensity, DailyExerciseRecommendation.Intensity.HIGH)
