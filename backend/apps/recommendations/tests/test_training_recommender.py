from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise
from django.contrib.auth import get_user_model
from apps.recommendations.services.training_recommender import suggest_exercise_for_today

User = get_user_model()


class TrainingRecommenderTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach_rec', email='cr@test.com', password='x', role='coach',
            first_name='C', last_name='R',
        )
        self.client_obj = Client.objects.create(
            first_name='Cl', last_name='R',
            email='clr@test.com', date_of_birth='1990-01-01', sex='M',
            height_m=1.70, initial_weight_kg=70,
        )
        self.ex1 = Exercise.objects.create(
            name='Mobility One', muscle_group='core', instructions='x',
            intensity=3, tags=['mobility'],
        )
        self.ex2 = Exercise.objects.create(
            name='Generic', muscle_group='back', instructions='y',
            intensity=5, tags=[],
        )

    def test_no_active_plan_returns_none_exercise_with_rationale(self):
        result = suggest_exercise_for_today(self.client_obj, date.today())
        self.assertIsNone(result['exercise'])
        self.assertIn('plan activo', result['rationale'])
        self.assertEqual(result['confidence'], Decimal('0'))

    def test_with_active_plan_returns_exercise_and_meta(self):
        start = date.today() - timedelta(days=5)
        end = date.today() + timedelta(days=5)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        result = suggest_exercise_for_today(self.client_obj, date.today())
        self.assertIn('rationale', result)
        self.assertIn('meta', result)
        self.assertIn('adherence_rate', result['meta'])
        self.assertIn('applied_rule', result['meta'])
        # May or may not have exercise depending on catalog
        self.assertIn('confidence', result)

    def test_high_pain_selects_mobility_or_low_impact(self):
        start = date.today() - timedelta(days=10)
        end = date.today() + timedelta(days=5)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        TrainingLog.objects.create(
            client=self.client_obj, date=date.today() - timedelta(days=1),
            execution_status=TrainingLog.ExecutionStatus.DONE,
            pain_level=7,
        )
        result = suggest_exercise_for_today(self.client_obj, date.today())
        self.assertEqual(result['meta']['applied_rule'], 'pain_high_mobility_low_impact')
        if result.get('exercise'):
            self.assertIn('mobility', result['exercise'].tags or [])
