"""
Tests for common permissions and utilities.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from apps.common.permissions import IsCoach, IsClient, IsCoachOrAssistant, get_client_from_user
from apps.clients.models import Client
from datetime import date

User = get_user_model()


class PermissionsTestCase(TestCase):
    """Test permission classes."""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass',
            role='coach'
        )
        self.assistant = User.objects.create_user(
            username='assistant',
            email='assistant@test.com',
            password='testpass',
            role='assistant'
        )
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='testpass',
            role='client'
        )
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='client@test.com',
            date_of_birth=date(1990, 1, 1),
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            user=self.client_user
        )
    
    def test_is_coach_permission(self):
        """Test IsCoach permission."""
        permission = IsCoach()
        
        request = self.factory.get('/')
        request.user = self.coach
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = self.assistant
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = self.client_user
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = None
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_client_permission(self):
        """Test IsClient permission."""
        permission = IsClient()
        
        request = self.factory.get('/')
        request.user = self.client_user
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = self.coach
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = None
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_coach_or_assistant_permission(self):
        """Test IsCoachOrAssistant permission."""
        permission = IsCoachOrAssistant()
        
        request = self.factory.get('/')
        request.user = self.coach
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = self.assistant
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = self.client_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_get_client_from_user(self):
        """Test get_client_from_user helper."""
        # Valid client user
        client = get_client_from_user(self.client_user)
        self.assertIsNotNone(client)
        self.assertEqual(client, self.client_obj)
        
        # Coach user (no client)
        client = get_client_from_user(self.coach)
        self.assertIsNone(client)
        
        # User without linked client
        orphan_user = User.objects.create_user(
            username='orphan',
            email='orphan@test.com',
            password='testpass',
            role='client'
        )
        client = get_client_from_user(orphan_user)
        self.assertIsNone(client)
        
        # None user
        client = get_client_from_user(None)
        self.assertIsNone(client)
