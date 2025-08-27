from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta

from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment
from .models import ClientSubscription

User = get_user_model()


class ClientPortalModelsTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@example.com',
            password='testpass123',
            role='coach'
        )
        
        self.client_obj = Client.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            date_of_birth=date(1990, 1, 1),
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            consent_checkbox=True
        )
        
        self.subscription = ClientSubscription.objects.create(
            client=self.client_obj,
            username='john_doe',
            password_hash='hashed_password',
            status='active',
            subscription_start=date.today(),
            subscription_end=date.today() + timedelta(days=30)
        )

    def test_client_subscription_str(self):
        self.assertEqual(
            str(self.subscription),
            f"{self.client_obj.full_name} - active"
        )

    def test_client_subscription_is_active(self):
        self.assertTrue(self.subscription.is_active)
        
        # Test expired subscription
        self.subscription.subscription_end = date.today() - timedelta(days=1)
        self.subscription.save()
        self.assertFalse(self.subscription.is_active)


class ClientPortalAPITest(APITestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@example.com',
            password='testpass123',
            role='coach'
        )
        
        self.client_obj = Client.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            date_of_birth=date(1990, 1, 1),
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            consent_checkbox=True
        )
        
        self.subscription = ClientSubscription.objects.create(
            client=self.client_obj,
            username='john_doe',
            password_hash='pbkdf2_sha256$600000$test$hash',
            status='active',
            subscription_start=date.today(),
            subscription_end=date.today() + timedelta(days=30)
        )
        
        # Create a diet plan
        self.diet_plan = DietPlan.objects.create(
            title='Test Diet Plan',
            description='Test description',
            goal='cut',
            daily_calories=1800,
            protein_pct=30.0,
            carbs_pct=40.0,
            fat_pct=30.0,
            created_by=self.coach
        )
        
        # Assign diet plan to client
        self.assignment = PlanAssignment.objects.create(
            client=self.client_obj,
            plan_type='diet',
            diet_plan=self.diet_plan,
            start_date=date.today(),
            is_active=True,
            assigned_by=self.coach
        )

    def test_client_login_success(self):
        """Test successful client login"""
        url = reverse('client-login')
        data = {
            'username': 'john_doe',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('client', response.data)

    def test_client_login_invalid_credentials(self):
        """Test client login with invalid credentials"""
        url = reverse('client-login')
        data = {
            'username': 'john_doe',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_dashboard_requires_auth(self):
        """Test that client dashboard requires authentication"""
        url = reverse('client-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_plan_access_requires_auth(self):
        """Test that plan access requires authentication"""
        url = reverse('client-plan-detail', kwargs={'pk': self.assignment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
