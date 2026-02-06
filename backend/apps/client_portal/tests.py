from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta

from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment
from apps.tracking.models import DailyExerciseRecommendation, TrainingLog, ClientProgressionState
from apps.catalogs.models import Exercise
from .models import ClientAccessLog

User = get_user_model()


class ClientPortalModelsTest(TestCase):
    """Tests for client portal models (ClientAccessLog)."""
    
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
            height_m=1.75,
            initial_weight_kg=80.0,
            consent_checkbox=True
        )


class ClientPortalAPITest(APITestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@example.com',
            password='testpass123',
            role='coach'
        )
        
        # Create client user
        self.client_user = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='testpass123',
            role='client',
            first_name='John',
            last_name='Doe'
        )
        
        self.client_obj = Client.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            date_of_birth=date(1990, 1, 1),
            sex='M',
            height_m=1.75,
            initial_weight_kg=80.0,
            consent_checkbox=True,
            user=self.client_user  # Link client to user
        )
        
        # Create another client user for isolation testing
        self.other_client_user = User.objects.create_user(
            username='jane_smith',
            email='jane@example.com',
            password='testpass123',
            role='client',
            first_name='Jane',
            last_name='Smith'
        )
        
        self.other_client = Client.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            date_of_birth=date(1992, 5, 15),
            sex='F',
            height_m=1.65,
            initial_weight_kg=65.0,
            consent_checkbox=True,
            user=self.other_client_user
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
        """Test successful client login with unified JWT auth"""
        url = reverse('users:client_token_obtain')  # Using unified endpoint in users app
        data = {
            'username': self.client_user.username,
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('client', response.data)
        self.assertEqual(response.data['client']['id'], self.client_obj.id)

    def test_client_login_invalid_credentials(self):
        """Test client login with invalid credentials"""
        url = reverse('users:client_token_obtain')
        data = {
            'username': self.client_user.username,
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_login_non_client_user(self):
        """Test that non-client users cannot login to client portal"""
        url = reverse('users:client_token_obtain')
        data = {
            'username': 'coach',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        # Should return validation error, not 403
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_login_no_client_profile(self):
        """Test login fails if user has no linked Client profile"""
        # Create user without client profile
        orphan_user = User.objects.create_user(
            username='orphan',
            email='orphan@example.com',
            password='testpass123',
            role='client'
        )
        
        url = reverse('users:client_token_obtain')
        data = {
            'username': 'orphan',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_dashboard_requires_auth(self):
        """Test that client dashboard requires authentication"""
        url = reverse('client-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_dashboard_access(self):
        """Test that authenticated client can access their dashboard"""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('client-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.client_obj.id)

    def test_client_can_only_see_own_plans(self):
        """Test that client can only see their own plan assignments"""
        # Create assignment for other client
        other_assignment = PlanAssignment.objects.create(
            client=self.other_client,
            plan_type='diet',
            diet_plan=self.diet_plan,
            start_date=date.today(),
            is_active=True,
            assigned_by=self.coach
        )
        
        self.client.force_authenticate(user=self.client_user)
        url = reverse('client-plan-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see own assignment
        assignment_ids = [a['id'] for a in response.data['results']] if 'results' in response.data else [a['id'] for a in response.data]
        self.assertIn(self.assignment.id, assignment_ids)
        self.assertNotIn(other_assignment.id, assignment_ids)

    def test_client_cannot_access_other_client_data(self):
        """Test that client cannot access another client's data"""
        self.client.force_authenticate(user=self.client_user)
        
        # Try to access other client's assignment
        other_assignment = PlanAssignment.objects.create(
            client=self.other_client,
            plan_type='diet',
            diet_plan=self.diet_plan,
            start_date=date.today(),
            is_active=True,
            assigned_by=self.coach
        )
        
        url = reverse('client-plan-detail', kwargs={'pk': other_assignment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_client_plan_access_requires_auth(self):
        """Test that plan access requires authentication"""
        url = reverse('client-plan-detail', kwargs={'pk': self.assignment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_access_log_created_on_plan_access(self):
        """Test that ClientAccessLog is created when client accesses plans"""
        initial_count = ClientAccessLog.objects.count()
        
        # Login first
        self.client.force_authenticate(user=self.client_user)
        
        # Access a plan detail (diet plan detail action)
        url = reverse('client-plan-diet-plan-detail', kwargs={'pk': self.assignment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that access log was created
        self.assertEqual(ClientAccessLog.objects.count(), initial_count + 1)
        log_entry = ClientAccessLog.objects.latest('created_at')
        self.assertEqual(log_entry.client, self.client_obj)
        self.assertEqual(log_entry.action, 'view_plan')
    
    def test_coach_cannot_access_client_portal_endpoints(self):
        """Test that coach cannot access client portal endpoints."""
        self.client.force_authenticate(user=self.coach)
        
        # Try to access client dashboard
        url = reverse('client-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to access client plans
        url = reverse('client-plan-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_cannot_access_coach_endpoints(self):
        """Test that client cannot access coach endpoints."""
        self.client.force_authenticate(user=self.client_user)
        
        # Try to access clients list
        url = '/api/clients/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to access diet plans
        url = '/api/diet-plans/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_complete_daily_exercise_creates_training_log_and_updates_progression(self):
        """POST complete with post-workout body creates TrainingLog and updates ProgressionState (closed-loop V1.1)."""
        exercise = Exercise.objects.create(
            name='Test exercise',
            muscle_group='quads',
            difficulty='beginner',
            intensity=5,
            instructions='Do it.',
        )
        rec = DailyExerciseRecommendation.objects.create(
            client=self.client_obj,
            date=date.today(),
            exercise=exercise,
            intensity='moderate',
            type='strength',
            rationale='Test',
            status=DailyExerciseRecommendation.Status.RECOMMENDED,
        )
        self.client.force_authenticate(user=self.client_user)
        url = reverse('client-me-daily-exercise-complete', kwargs={'pk': rec.pk})
        data = {
            'rpe': 3,
            'energy_level': 8,
            'pain_level': 1,
            'notes': 'Felt good',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recommendation']['status'], 'completed')
        self.assertIn('training_log_id', response.data)
        self.assertIn('progression_update', response.data)
        self.assertIn('message', response.data['progression_update'])

        log = TrainingLog.objects.filter(client=self.client_obj, date=date.today()).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.rpe, 3)
        self.assertEqual(log.energy_level, 8)
        self.assertEqual(log.pain_level, 1)
        self.assertEqual(log.execution_status, TrainingLog.ExecutionStatus.DONE)
        self.assertEqual(log.recommendation_version, 'daily_exercise_v1.1')

        state = ClientProgressionState.objects.filter(client=self.client_obj).first()
        self.assertIsNotNone(state)
        self.assertIsNotNone(response.data['progression_update']['outcome_score'])
