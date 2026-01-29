"""Tests for TrainingLog and DietLog: client me endpoints, coach access, constraints."""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.clients.models import Client
from apps.catalogs.models import Exercise
from apps.plans.models import PlanCycle
from .models import TrainingLog, DietLog

User = get_user_model()


class TrainingLogDietLogTestBase(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach1',
            email='coach1@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='One',
        )
        self.client_user_a = User.objects.create_user(
            username='client_a',
            email='client_a@test.com',
            password='testpass123',
            role='client',
            first_name='Client',
            last_name='A',
        )
        self.client_user_b = User.objects.create_user(
            username='client_b',
            email='client_b@test.com',
            password='testpass123',
            role='client',
            first_name='Client',
            last_name='B',
        )
        self.client_a = Client.objects.create(
            first_name='A',
            last_name='User',
            email='a@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=170,
            initial_weight_kg=70,
            user=self.client_user_a,
        )
        self.client_b = Client.objects.create(
            first_name='B',
            last_name='User',
            email='b@test.com',
            date_of_birth='1992-01-01',
            sex='F',
            height_cm=165,
            initial_weight_kg=60,
            user=self.client_user_b,
        )
        self.exercise = Exercise.objects.create(
            name='Squat',
            muscle_group='quads',
            equipment_type='barra',
            difficulty='beginner',
            instructions='Do squats',
        )


class ClientMeEndpointTests(TrainingLogDietLogTestBase):
    """1) Client can create their own TrainingLog and DietLog (me endpoints)."""

    def test_client_can_create_own_training_log_via_me(self):
        self.api.force_authenticate(user=self.client_user_a)
        log_date = date.today().isoformat()
        payload = {
            'execution_status': 'done',
            'duration_minutes': 45,
            'rpe': 7,
            'notes': 'Felt good',
        }
        response = self.api.post(
            f'/api/client/me/training-log/?date={log_date}',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrainingLog.objects.filter(client=self.client_a).count(), 1)
        log = TrainingLog.objects.get(client=self.client_a, date=date.today())
        self.assertEqual(log.execution_status, 'done')
        self.assertEqual(log.duration_minutes, 45)

    def test_client_can_create_own_diet_log_via_me(self):
        self.api.force_authenticate(user=self.client_user_a)
        log_date = date.today().isoformat()
        payload = {
            'adherence_percent': 85,
            'hunger_level': 5,
            'notes': 'On track',
        }
        response = self.api.post(
            f'/api/client/me/diet-log/?date={log_date}',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DietLog.objects.filter(client=self.client_a).count(), 1)
        log = DietLog.objects.get(client=self.client_a, date=date.today())
        self.assertEqual(log.adherence_percent, 85)

    def test_client_me_get_returns_null_when_no_log(self):
        self.api.force_authenticate(user=self.client_user_a)
        response = self.api.get('/api/client/me/training-log/?date=2026-01-28')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data.get('data'))

    def test_client_me_upsert_training_log(self):
        """Unique constraint: second POST same (client, date) updates (upsert)."""
        self.api.force_authenticate(user=self.client_user_a)
        log_date = '2026-01-28'
        self.api.post(
            f'/api/client/me/training-log/?date={log_date}',
            {'execution_status': 'partial', 'duration_minutes': 20},
            format='json',
        )
        response = self.api.post(
            f'/api/client/me/training-log/?date={log_date}',
            {'execution_status': 'done', 'duration_minutes': 45},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrainingLog.objects.filter(client=self.client_a).count(), 1)
        log = TrainingLog.objects.get(client=self.client_a, date=date(2026, 1, 28))
        self.assertEqual(log.execution_status, 'done')
        self.assertEqual(log.duration_minutes, 45)


class ClientCannotAccessOtherOrCoachEndpointsTests(TrainingLogDietLogTestBase):
    """2) Client cannot create logs for another client. 3) Client cannot read another client's logs."""

    def test_client_cannot_create_via_coach_endpoint_gets_403(self):
        """Client POST to coach endpoint should be 403 (cannot create for any client)."""
        self.api.force_authenticate(user=self.client_user_a)
        payload = {
            'client': self.client_a.id,
            'date': date.today().isoformat(),
            'execution_status': 'done',
        }
        response = self.api.post(
            '/api/tracking/training-logs/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TrainingLog.objects.count(), 0)

    def test_client_cannot_list_logs_via_coach_endpoint(self):
        """Client GET coach endpoint gets 403."""
        self.api.force_authenticate(user=self.client_user_a)
        response = self.api.get('/api/tracking/training-logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_read_other_client_log_via_me(self):
        """Client A has a log; client B cannot see it (me returns only own)."""
        TrainingLog.objects.create(
            client=self.client_a,
            date=date(2026, 1, 28),
            execution_status='done',
        )
        self.api.force_authenticate(user=self.client_user_b)
        response = self.api.get('/api/client/me/training-log/?date=2026-01-28')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsNone(data.get('data'))


class CoachCanFilterLogsTests(TrainingLogDietLogTestBase):
    """5) Coach can list logs by client filter."""

    def test_coach_can_list_logs_filtered_by_client(self):
        TrainingLog.objects.create(
            client=self.client_a,
            date=date.today(),
            execution_status='done',
        )
        TrainingLog.objects.create(
            client=self.client_b,
            date=date.today(),
            execution_status='partial',
        )
        self.api.force_authenticate(user=self.coach)
        response = self.api.get(
            f'/api/tracking/training-logs/?client={self.client_a.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['client'], self.client_a.id)

    def test_coach_can_create_training_log_for_client(self):
        self.api.force_authenticate(user=self.coach)
        payload = {
            'client': self.client_a.id,
            'date': date.today().isoformat(),
            'execution_status': 'done',
            'suggested_exercise': self.exercise.id,
        }
        response = self.api.post(
            '/api/tracking/training-logs/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrainingLog.objects.filter(client=self.client_a).count(), 1)


class UniqueConstraintTests(TrainingLogDietLogTestBase):
    """4) Unique constraint (client, date): duplicates not created; upsert works."""

    def test_diet_log_unique_per_client_date(self):
        DietLog.objects.create(
            client=self.client_a,
            date=date(2026, 1, 28),
            adherence_percent=80,
        )
        second = DietLog(
            client=self.client_a,
            date=date(2026, 1, 28),
            adherence_percent=90,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            second.save()
