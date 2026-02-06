"""Unit tests for daily exercise recommendation V1 (heuristic engine)."""
from datetime import date, timedelta
from django.test import TestCase
from apps.clients.models import Client
from apps.tracking.models import TrainingLog, DailyExerciseRecommendation
from apps.catalogs.models import Exercise
from django.contrib.auth import get_user_model
from apps.recommendations.services.daily_exercise import generate_daily_recommendation

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
        self.assertIn('rationale', rec.rationale or '')
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
