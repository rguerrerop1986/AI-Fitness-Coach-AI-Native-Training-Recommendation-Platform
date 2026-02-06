from datetime import date, timedelta
from django.test import TestCase
from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise
from django.contrib.auth import get_user_model
from apps.recommendations.selectors import (
    get_active_plan_cycle_for_client,
    get_recent_training_logs,
    compute_pain_trend,
    compute_adherence_rate,
    get_exercises_for_recommendation,
)

User = get_user_model()


class SelectorsTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach_sel', email='c@test.com', password='x', role='coach',
            first_name='C', last_name='O',
        )
        self.client_obj = Client.objects.create(
            first_name='Cl', last_name='X',
            email='cl@test.com', date_of_birth='1990-01-01', sex='M',
            height_m=1.70, initial_weight_kg=70,
        )

    def test_get_active_plan_cycle_none_when_no_cycle(self):
        cycle = get_active_plan_cycle_for_client(self.client_obj, date.today())
        self.assertIsNone(cycle)

    def test_get_active_plan_cycle_returns_cycle_covering_date(self):
        start = date.today() - timedelta(days=5)
        end = date.today() + timedelta(days=5)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        cycle = get_active_plan_cycle_for_client(self.client_obj, date.today())
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle.client_id, self.client_obj.id)

    def test_get_recent_training_logs_returns_ordered_by_date_desc(self):
        for i in range(3):
            TrainingLog.objects.create(
                client=self.client_obj, date=date.today() - timedelta(days=i),
                execution_status=TrainingLog.ExecutionStatus.NOT_DONE,
            )
        logs = list(get_recent_training_logs(self.client_obj, days=14))
        self.assertEqual(len(logs), 3)
        self.assertGreaterEqual(logs[0].date, logs[1].date)
        self.assertGreaterEqual(logs[1].date, logs[2].date)

    def test_compute_pain_trend_empty(self):
        self.assertIsNone(compute_pain_trend([]))

    def test_compute_pain_trend_high_when_last_pain_ge_6(self):
        log = TrainingLog(client=self.client_obj, date=date.today(), pain_level=7)
        log.execution_status = TrainingLog.ExecutionStatus.DONE
        self.assertEqual(compute_pain_trend([log]), 'high')

    def test_compute_adherence_rate_zero_when_no_logs(self):
        self.assertEqual(compute_adherence_rate([]), 0.0)

    def test_compute_adherence_rate_half_when_half_done(self):
        logs = [
            TrainingLog(client=self.client_obj, date=date.today(), execution_status=TrainingLog.ExecutionStatus.DONE),
            TrainingLog(client=self.client_obj, date=date.today() - timedelta(days=1), execution_status=TrainingLog.ExecutionStatus.NOT_DONE),
        ]
        self.assertEqual(compute_adherence_rate(logs), 0.5)

    def test_get_exercises_for_recommendation_filters_intensity_and_tags(self):
        Exercise.objects.create(name='Low', muscle_group='core', instructions='x', intensity=3, tags=['mobility'])
        Exercise.objects.create(name='High', muscle_group='core', instructions='y', intensity=8, tags=[])
        qs = get_exercises_for_recommendation(max_intensity=4, tags_any=['mobility'])
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, 'Low')
