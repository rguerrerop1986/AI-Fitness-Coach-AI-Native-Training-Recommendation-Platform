"""Tests for client creation with portal user."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Client

User = get_user_model()


class ClientCreateWithPortalUserTest(TestCase):
    """When coach creates a client with password, a User is created and linked."""

    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test',
        )

    def test_create_client_creates_portal_user(self):
        self.api.force_authenticate(user=self.coach)
        payload = {
            'first_name': 'Raul',
            'last_name': 'Client',
            'date_of_birth': '1990-01-01',
            'sex': 'M',
            'email': 'raul.client@test.com',
            'phone': '+52123456789',
            'height_m': 1.75,
            'initial_weight_kg': 80,
            'notes': '',
            'consent_checkbox': True,
            'emergency_contact': 'Jane - +52987654321 (Spouse)',
            'password': 'securepass123',
        }
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        client = Client.objects.get(email='raul.client@test.com')
        self.assertIsNotNone(client.user_id)
        user = client.user
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertEqual(user.email, 'raul.client@test.com')
        self.assertTrue(user.check_password('securepass123'))
        self.assertEqual(response.data.get('portal_username'), user.username)
        self.assertTrue(response.data.get('has_portal_access'))

    def test_create_client_requires_password(self):
        self.api.force_authenticate(user=self.coach)
        payload = {
            'first_name': 'No',
            'last_name': 'Password',
            'date_of_birth': '1995-01-01',
            'sex': 'F',
            'email': 'nopass@test.com',
            'phone': '+52111111111',
            'height_m': 1.65,
            'initial_weight_kg': 60,
            'notes': '',
            'consent_checkbox': True,
            'emergency_contact': 'Someone',
        }
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json() or {}
        self.assertTrue('password' in data or 'detail' in data, 'Expected password error in response')

    def test_create_client_height_m_in_meters(self):
        """Height must be in meters (0.50-2.50). Reject cm (e.g. 185)."""
        self.api.force_authenticate(user=self.coach)
        # Valid: 1.85 m
        payload = {
            'first_name': 'Valid',
            'last_name': 'Height',
            'date_of_birth': '1990-01-01',
            'sex': 'M',
            'email': 'valid.height@test.com',
            'phone': '+52123456789',
            'height_m': 1.85,
            'initial_weight_kg': 80,
            'notes': '',
            'consent_checkbox': True,
            'emergency_contact': 'Jane',
            'password': 'securepass123',
        }
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        client = Client.objects.get(email='valid.height@test.com')
        self.assertEqual(float(client.height_m), 1.85)

        # Invalid: 185 (cm) rejected
        payload['email'] = 'invalid.height@test.com'
        payload['height_m'] = 185
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('height_m', response.json())

    def test_create_client_level_saved(self):
        """Client level (beginner/intermediate/advanced) is saved."""
        self.api.force_authenticate(user=self.coach)
        payload = {
            'first_name': 'Level',
            'last_name': 'User',
            'date_of_birth': '1990-01-01',
            'sex': 'M',
            'email': 'level.user@test.com',
            'phone': '+52123456789',
            'height_m': 1.75,
            'initial_weight_kg': 70,
            'level': 'intermediate',
            'notes': '',
            'consent_checkbox': True,
            'emergency_contact': 'Jane',
            'password': 'securepass123',
        }
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('level'), 'intermediate')


class ClientSetPasswordTest(TestCase):
    """Test setting password for existing clients."""

    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test',
        )
        self.client_obj = Client.objects.create(
            first_name='Existing',
            last_name='Client',
            email='existing@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=80,
            consent_checkbox=True,
        )

    def test_set_password_creates_user_if_none(self):
        """If client has no user, set_password creates one."""
        self.api.force_authenticate(user=self.coach)
        self.assertIsNone(self.client_obj.user_id)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/set_password/',
            {'password': 'newpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_obj.refresh_from_db()
        self.assertIsNotNone(self.client_obj.user_id)
        user = self.client_obj.user
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertTrue(user.check_password('newpass123'))
        self.assertEqual(response.data.get('portal_username'), user.username)

    def test_set_password_updates_existing_user(self):
        """If client has user, set_password updates the password."""
        # Create user first
        user = User.objects.create_user(
            username='existing@test.com',
            email='existing@test.com',
            password='oldpass123',
            role=User.Role.CLIENT,
        )
        self.client_obj.user = user
        self.client_obj.save()
        self.api.force_authenticate(user=self.coach)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/set_password/',
            {'password': 'newpass456'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass456'))
        self.assertFalse(user.check_password('oldpass123'))

    def test_set_password_requires_min_length(self):
        """Password must be at least 8 characters."""
        self.api.force_authenticate(user=self.coach)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/set_password/',
            {'password': 'short'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ClientDeactivateTest(TestCase):
    """Deactivate client: soft delete + cancel future appointments."""

    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test',
        )
        self.client_obj = Client.objects.create(
            first_name='Deact',
            last_name='Client',
            email='deact@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=80,
            consent_checkbox=True,
        )

    def test_deactivate_sets_client_inactive_and_returns_count(self):
        self.api.force_authenticate(user=self.coach)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/deactivate/',
            {'reason': 'Se fue del programa'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_obj.refresh_from_db()
        self.assertFalse(self.client_obj.is_active)
        self.assertIsNotNone(self.client_obj.deactivated_at)
        self.assertEqual(self.client_obj.deactivated_by_id, self.coach.id)
        self.assertEqual(self.client_obj.deactivation_reason, 'Se fue del programa')
        self.assertIn('cancelled_appointments_count', response.data)
        self.assertEqual(response.data['cancelled_appointments_count'], 0)

    def test_deactivate_cancels_future_appointments_only(self):
        from django.utils import timezone
        from datetime import timedelta
        from apps.appointments.models import Appointment

        future = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            status=Appointment.Status.SCHEDULED,
            price=100,
        )
        no_show_future = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=2),
            duration_minutes=60,
            status=Appointment.Status.NO_SHOW,
            price=100,
        )
        past = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() - timedelta(days=1),
            duration_minutes=60,
            status=Appointment.Status.SCHEDULED,
            price=100,
        )
        already_cancelled = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=3),
            duration_minutes=60,
            status=Appointment.Status.CANCELLED,
            price=100,
        )

        self.api.force_authenticate(user=self.coach)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/deactivate/',
            {'reason': 'Baja'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('cancelled_appointments_count'), 2)

        future.refresh_from_db()
        no_show_future.refresh_from_db()
        past.refresh_from_db()
        already_cancelled.refresh_from_db()

        self.assertEqual(future.status, Appointment.Status.CANCELLED)
        self.assertEqual(no_show_future.status, Appointment.Status.CANCELLED)
        self.assertEqual(past.status, Appointment.Status.SCHEDULED)
        self.assertEqual(already_cancelled.status, Appointment.Status.CANCELLED)

    def test_reactivate_clears_deactivation_fields(self):
        self.client_obj.is_active = False
        self.client_obj.save()
        self.api.force_authenticate(user=self.coach)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/reactivate/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_obj.refresh_from_db()
        self.assertTrue(self.client_obj.is_active)
        self.assertIsNone(self.client_obj.deactivated_at)
        self.assertIsNone(self.client_obj.deactivated_by_id)


class BlockCreateCheckInPlanForInactiveClientTest(TestCase):
    """Creating check-in or plan for inactive client returns 409."""

    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test',
        )
        self.client_obj = Client.objects.create(
            first_name='Inact',
            last_name='Client',
            email='inact@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=80,
            consent_checkbox=True,
            is_active=False,
        )

    def test_create_checkin_for_inactive_returns_409(self):
        from apps.tracking.tests import _structural_checkin_payload
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_obj.id)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('detail', response.json())
        self.assertIn('inactivo', response.json()['detail'].lower())

    def test_create_plan_for_inactive_returns_409(self):
        self.api.force_authenticate(user=self.coach)
        data = {
            'client': self.client_obj.id,
            'period_days': 14,
            'goal': 'fat_loss',
        }
        response = self.api.post('/api/plans/plan-cycles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('detail', response.json())
        self.assertIn('inactivo', response.json()['detail'].lower())

    def test_create_checkin_for_active_returns_201(self):
        self.client_obj.is_active = True
        self.client_obj.save()
        from apps.tracking.tests import _structural_checkin_payload
        self.api.force_authenticate(user=self.coach)
        payload = _structural_checkin_payload(self.client_obj.id)
        response = self.api.post(
            f'/api/clients/{self.client_obj.id}/check-ins/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_plan_for_active_returns_201(self):
        self.client_obj.is_active = True
        self.client_obj.save()
        self.api.force_authenticate(user=self.coach)
        data = {
            'client': self.client_obj.id,
            'period_days': 14,
            'goal': 'fat_loss',
        }
        response = self.api.post('/api/plans/plan-cycles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ClientListDefaultActiveTest(TestCase):
    """List clients: default is active only; ?is_active=false shows inactives."""

    def setUp(self):
        self.api = APIClient()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test',
        )
        Client.objects.create(
            first_name='Active',
            last_name='One',
            email='active@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_m=1.75,
            initial_weight_kg=80,
            consent_checkbox=True,
            is_active=True,
        )
        Client.objects.create(
            first_name='Inactive',
            last_name='Two',
            email='inactive@test.com',
            date_of_birth='1990-01-01',
            sex='F',
            height_m=1.65,
            initial_weight_kg=60,
            consent_checkbox=True,
            is_active=False,
        )

    def test_list_default_shows_only_active(self):
        self.api.force_authenticate(user=self.coach)
        response = self.api.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json() if hasattr(response, 'json') else response.data
        results = data.get('results', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        emails = [c['email'] for c in results]
        self.assertIn('active@test.com', emails)
        self.assertNotIn('inactive@test.com', emails)

    def test_list_with_is_active_false_shows_inactive(self):
        self.api.force_authenticate(user=self.coach)
        response = self.api.get('/api/clients/?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', []) if isinstance(response.data, dict) else response.data
        emails = [c['email'] for c in results]
        self.assertIn('inactive@test.com', emails)
