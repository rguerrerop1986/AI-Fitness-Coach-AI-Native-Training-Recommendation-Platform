"""Tests for TrainingLog and DietLog: client me endpoints, coach access, constraints."""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.clients.models import Client
from apps.catalogs.models import Exercise
from apps.plans.models import PlanCycle
from .models import CheckIn, TrainingLog, DietLog

User = get_user_model()


def _structural_checkin_payload(client_id, **overrides):
    """Payload ESTRUCTURAL mínimo válido para POST."""
    from decimal import Decimal
    base = {
        'client_id': client_id,
        'date': '2026-02-04',
        'weight_kg': 75.5,
        'height_m': 1.75,
        'rc_termino': 140,
        'rc_1min': 110,
        'skinfolds': {
            'triceps': {'m1': 10, 'm2': 10.5, 'm3': 10.2, 'avg': 10.23},
            'subscapular': {'m1': 12, 'm2': 12.1, 'm3': 12.2, 'avg': 12.10},
            'suprailiac': {'m1': 14, 'm2': 14.2, 'm3': 14.1, 'avg': 14.10},
            'abdominal': {'m1': 18, 'm2': 18.5, 'm3': 18.2, 'avg': 18.23},
            'ant_thigh': {'m1': 16, 'm2': 16.3, 'm3': 16.1, 'avg': 16.13},
            'calf': {'m1': 9, 'm2': 9.2, 'm3': 9.1, 'avg': 9.10},
        },
        'diameters': {
            'femoral': {'l': 9, 'r': 9.1, 'avg': 9.05},
            'humeral': {'l': 7, 'r': 7.2, 'avg': 7.10},
            'styloid': {'l': 5, 'r': 5.1, 'avg': 5.05},
        },
        'perimeters': {
            'waist': 80,
            'abdomen': 85,
            'calf': 35,
            'hip': 98,
            'chest': 100,
            'arm': {'relaxed': 30, 'flexed': 32},
            'thigh': {'relaxed': 52, 'flexed': 54},
        },
        'feedback': {
            'rpe': 5,
            'fatigue': 5,
            'diet_adherence_pct': 80,
            'training_adherence_pct': 85,
            'notes': 'Ok',
        },
    }
    base.update(overrides or {})
    return base


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
            height_m=1.70,
            initial_weight_kg=70,
            user=self.client_user_a,
        )
        self.client_b = Client.objects.create(
            first_name='B',
            last_name='User',
            email='b@test.com',
            date_of_birth='1992-01-01',
            sex='F',
            height_m=1.65,
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


class CoachDashboardTests(TrainingLogDietLogTestBase):
    """AI Coach Dashboard: coach-only, returns high_pain, not_done_streak, adherence_trend, by_client."""

    def test_coach_dashboard_returns_200_and_structure(self):
        start = date.today() - timedelta(days=5)
        end = date.today() + timedelta(days=5)
        cycle = PlanCycle.objects.create(
            client=self.client_a, coach=self.coach,
            start_date=start, end_date=end, status=PlanCycle.Status.ACTIVE,
        )
        TrainingLog.objects.create(
            client=self.client_a, date=date.today(),
            plan_cycle=cycle, execution_status='done', pain_level=7,
        )
        self.api.force_authenticate(user=self.coach)
        response = self.api.get('/api/tracking/coach-dashboard/?days=7')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('high_pain_clients', data)
        self.assertIn('not_done_streak_clients', data)
        self.assertIn('adherence_trend', data)
        self.assertIn('by_client', data)
        self.assertEqual(len(data['high_pain_clients']), 1)
        self.assertEqual(data['high_pain_clients'][0]['pain_level'], 7)


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


class CheckInStructuralTests(TrainingLogDietLogTestBase):
    """Check-in ESTRUCTURAL: nested payload, validation, GET devuelve rc_1min y promedios."""

    def test_coach_can_create_structural_checkin_nested_payload(self):
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_a.id)
        response = self.api.post(
            f'/api/clients/{self.client_a.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['weight_kg'], '75.5')
        self.assertEqual(data['height_m'], '1.75')
        self.assertEqual(data['rc_termino'], 140)
        self.assertEqual(data['rc_1min'], 110)
        self.assertIn('skinfold_triceps_avg', data)
        self.assertIn('diameter_femoral_avg', data)
        self.assertIn('perimeter_waist', data)
        # Promedios persistidos
        self.assertEqual(CheckIn.objects.count(), 1)
        c = CheckIn.objects.get(client=self.client_a)
        self.assertEqual(float(c.skinfold_triceps_avg), 10.23)
        self.assertEqual(float(c.diameter_femoral_avg), 9.05)

    def test_get_checkin_returns_rc_1min_and_structural_fields(self):
        CheckIn.objects.create(
            client=self.client_a,
            date=date(2026, 2, 4),
            weight_kg=80,
            height_m=1.80,
            rc_termino=135,
            rc_1min_bpm=105,
            skinfold_triceps_1=10,
            skinfold_triceps_2=11,
            skinfold_triceps_3=10.5,
            skinfold_triceps_avg=10.5,
        )
        self.api.force_authenticate(user=self.coach)
        response = self.api.get(f'/api/clients/{self.client_a.id}/check-ins/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [data] if isinstance(data, dict) and 'id' in data else []
        self.assertGreaterEqual(len(results), 1)
        first = results[0]
        self.assertEqual(first['rc_1min'], 105)
        self.assertIn('skinfold_triceps_avg', first)

    def test_structural_checkin_validation_missing_required(self):
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_a.id)
        payload.pop('weight_kg')
        payload.pop('height_m')
        response = self.api.post(
            f'/api/clients/{self.client_a.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        err = response.json()
        self.assertIn('weight_kg', err)
        self.assertIn('height_m', err)

    def test_existing_checkin_without_structural_still_returns(self):
        """Registros previos sin campos ESTRUCTURAL no se rompen."""
        CheckIn.objects.create(
            client=self.client_a,
            date=date(2026, 1, 1),
            weight_kg=70,
            notes='Antiguo',
        )
        self.api.force_authenticate(user=self.coach)
        response = self.api.get(f'/api/clients/{self.client_a.id}/check-ins/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get('results', data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = [data] if isinstance(data, dict) and 'id' in data else []
        self.assertGreaterEqual(len(results), 1)
        first = results[0]
        self.assertEqual(first['weight_kg'], '70.0')
        self.assertEqual(first['notes'], 'Antiguo')


class CheckInBMITests(TrainingLogDietLogTestBase):
    """BMI (IMC): calculado en create, recalculado en update, height_m > 0 validado."""

    def test_bmi_is_calculated_on_create(self):
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_a.id)
        payload['weight_kg'] = 106.4
        payload['height_m'] = 1.85
        response = self.api.post(
            f'/api/clients/{self.client_a.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('bmi', data)
        expected_bmi = round(106.4 / (1.85 * 1.85), 2)
        self.assertEqual(float(data['bmi']), expected_bmi)
        c = CheckIn.objects.get(client=self.client_a, date='2026-02-04')
        self.assertEqual(float(c.bmi), expected_bmi)

    def test_bmi_recalculates_on_update_weight_or_height(self):
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_a.id)
        payload['weight_kg'] = 80
        payload['height_m'] = 1.80
        create_resp = self.api.post(
            f'/api/clients/{self.client_a.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        checkin_id = create_resp.json()['id']
        first_bmi = float(create_resp.json()['bmi'])
        self.assertAlmostEqual(first_bmi, round(80 / (1.80 * 1.80), 2), places=2)
        # Update weight and height
        update_resp = self.api.patch(
            f'/api/clients/{self.client_a.id}/check-ins/{checkin_id}/',
            {'weight_kg': 70, 'height_m': 1.75},
            format='json',
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        data = update_resp.json()
        self.assertIn('bmi', data)
        expected = round(70 / (1.75 * 1.75), 2)
        self.assertEqual(float(data['bmi']), expected)

    def test_invalid_height_raises_error(self):
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_a.id)
        payload['height_m'] = 0
        response = self.api.post(
            f'/api/clients/{self.client_a.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        err = response.json()
        self.assertIn('height_m', err)
