from datetime import date, timedelta
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise
from django.contrib.auth import get_user_model

User = get_user_model()


class GenerateDailyTrainingLogsTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach_cmd', email='cmd@test.com', password='x', role='coach',
            first_name='C', last_name='Cmd',
        )
        self.client_obj = Client.objects.create(
            first_name='Cl', last_name='Cmd',
            email='clcmd@test.com', date_of_birth='1990-01-01', sex='M',
            height_m=1.70, initial_weight_kg=70,
        )
        Exercise.objects.create(name='Ex', muscle_group='core', instructions='x', intensity=5, tags=[])

    def test_command_creates_log_for_active_cycle(self):
        start = date.today() - timedelta(days=2)
        end = date.today() + timedelta(days=2)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        out = StringIO()
        call_command('generate_daily_training_logs', stdout=out, dry_run=False)
        log = TrainingLog.objects.filter(client=self.client_obj, date=date.today()).first()
        self.assertIsNotNone(log)
        self.assertIn('created=', out.getvalue())

    def test_command_idempotent_second_run_does_not_fail(self):
        start = date.today() - timedelta(days=2)
        end = date.today() + timedelta(days=2)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        call_command('generate_daily_training_logs', dry_run=False)
        count_before = TrainingLog.objects.filter(client=self.client_obj, date=date.today()).count()
        call_command('generate_daily_training_logs', dry_run=False)
        count_after = TrainingLog.objects.filter(client=self.client_obj, date=date.today()).count()
        self.assertEqual(count_before, 1)
        self.assertEqual(count_after, 1)
