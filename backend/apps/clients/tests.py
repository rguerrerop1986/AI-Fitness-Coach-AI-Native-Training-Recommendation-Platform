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
            'height_cm': 175,
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
            'height_cm': 165,
            'initial_weight_kg': 60,
            'notes': '',
            'consent_checkbox': True,
            'emergency_contact': 'Someone',
        }
        response = self.api.post('/api/clients/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json() or {}
        self.assertTrue('password' in data or 'detail' in data, 'Expected password error in response')


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
            height_cm=175,
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
