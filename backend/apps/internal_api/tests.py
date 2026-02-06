from datetime import date, timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from apps.plans.models import PlanCycle
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise

User = get_user_model()


@override_settings(INTERNAL_API_TOKEN='test-internal-token-123')
class InternalAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = 'test-internal-token-123'
        self.coach = User.objects.create_user(
            username='coach_int', email='ci@test.com', password='x', role='coach',
            first_name='C', last_name='I',
        )
        self.client_obj = Client.objects.create(
            first_name='Cl', last_name='I',
            email='cli@test.com', date_of_birth='1990-01-01', sex='M',
            height_m=1.70, initial_weight_kg=70,
        )
        self.ex = Exercise.objects.create(name='Ex', muscle_group='core', instructions='x', intensity=5, tags=[])

    def _headers(self):
        return {'X-Internal-Token': self.token}

    def test_suggest_today_requires_auth(self):
        response = self.client.post(
            '/api/internal/recommendations/suggest-today/',
            {'client_id': self.client_obj.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suggest_today_success_with_token(self):
        start = date.today() - timedelta(days=2)
        end = date.today() + timedelta(days=2)
        PlanCycle.objects.create(
            client=self.client_obj, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        response = self.client.post(
            '/api/internal/recommendations/suggest-today/',
            {'client_id': self.client_obj.id},
            format='json',
            HTTP_X_INTERNAL_TOKEN=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rationale', response.data)
        self.assertIn('meta', response.data)

    def test_tracking_context_requires_token(self):
        response = self.client.get('/api/internal/tracking/context/', {'client_id': self.client_obj.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tracking_context_success(self):
        response = self.client.get(
            '/api/internal/tracking/context/',
            {'client_id': self.client_obj.id, 'days': 7},
            HTTP_X_INTERNAL_TOKEN=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('logs', response.data)
        self.assertIn('adherence_rate', response.data)

    def test_tracking_feedback_creates_or_updates_log(self):
        today = date.today().isoformat()
        response = self.client.post(
            '/api/internal/tracking/feedback/',
            {
                'client_id': self.client_obj.id,
                'date': today,
                'execution_status': 'done',
                'rpe': 7,
                'notes': 'Good',
            },
            format='json',
            HTTP_X_INTERNAL_TOKEN=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = TrainingLog.objects.filter(client=self.client_obj, date=date.today()).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.execution_status, TrainingLog.ExecutionStatus.DONE)
        self.assertEqual(log.rpe, 7)

    def test_coach_summary_requires_token(self):
        response = self.client.get('/api/internal/coach/summary/', {'coach_id': self.coach.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_coach_summary_success(self):
        response = self.client.get(
            '/api/internal/coach/summary/',
            {'coach_id': self.coach.id, 'days': 7},
            HTTP_X_INTERNAL_TOKEN=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('high_pain_clients', response.data)
        self.assertIn('adherence_trend', response.data)

    def test_catalog_exercises_success(self):
        response = self.client.get(
            '/api/internal/catalog/exercises/',
            {'limit': 5},
            HTTP_X_INTERNAL_TOKEN=self.token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
