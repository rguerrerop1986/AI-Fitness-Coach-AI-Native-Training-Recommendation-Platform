"""
Tests for PlanCycle model and endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from apps.clients.models import Client
from apps.plans.models import PlanCycle, PlanAssignment, DietPlan, WorkoutPlan

User = get_user_model()


class PlanCycleModelTestCase(TestCase):
    """Test PlanCycle model business rules."""
    
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass',
            role='coach'
        )
        self.client_obj = Client.objects.create(
            first_name='Test',
            last_name='Client',
            email='client@test.com',
            date_of_birth=date(1990, 1, 1),
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0
        )
    
    def test_create_plan_cycle(self):
        """Test creating a basic PlanCycle."""
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            cadence=PlanCycle.Cadence.WEEKLY,
            status=PlanCycle.Status.DRAFT
        )
        
        self.assertEqual(cycle.client, self.client_obj)
        self.assertEqual(cycle.coach, self.coach)
        self.assertEqual(cycle.cadence, PlanCycle.Cadence.WEEKLY)
        self.assertEqual(cycle.status, PlanCycle.Status.DRAFT)
    
    def test_no_overlapping_active_cycles(self):
        """Test that overlapping active cycles are rejected."""
        # Create first active cycle
        PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            status=PlanCycle.Status.ACTIVE
        )
        
        # Try to create overlapping active cycle
        with self.assertRaises(ValidationError):
            cycle = PlanCycle(
                client=self.client_obj,
                coach=self.coach,
                start_date=date.today() + timedelta(days=3),
                end_date=date.today() + timedelta(days=10),
                status=PlanCycle.Status.ACTIVE
            )
            cycle.clean()
            cycle.save()
    
    def test_draft_cycles_can_overlap(self):
        """Test that draft cycles can overlap."""
        PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            status=PlanCycle.Status.DRAFT
        )
        
        # Should not raise error
        cycle2 = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today() + timedelta(days=3),
            end_date=date.today() + timedelta(days=10),
            status=PlanCycle.Status.DRAFT
        )
        
        self.assertIsNotNone(cycle2)
    
    def test_end_date_after_start_date(self):
        """Test that end_date must be after start_date."""
        with self.assertRaises(ValidationError):
            cycle = PlanCycle(
                client=self.client_obj,
                coach=self.coach,
                start_date=date.today(),
                end_date=date.today() - timedelta(days=1),
                status=PlanCycle.Status.DRAFT
            )
            cycle.clean()
    
    def test_is_active_property(self):
        """Test is_active property."""
        # Active cycle within date range
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=6),
            status=PlanCycle.Status.ACTIVE
        )
        self.assertTrue(cycle.is_active)
        
        # Active cycle but past end date
        cycle2 = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=3),
            status=PlanCycle.Status.ACTIVE
        )
        self.assertFalse(cycle2.is_active)
        
        # Draft cycle
        cycle3 = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            status=PlanCycle.Status.DRAFT
        )
        self.assertFalse(cycle3.is_active)


class PlanCycleAPITestCase(APITestCase):
    """Test PlanCycle API endpoints."""
    
    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass',
            role='coach'
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
        self.cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            status=PlanCycle.Status.ACTIVE
        )
    
    def test_coach_can_create_plan_cycle(self):
        """Test coach can create PlanCycle."""
        self.client.force_authenticate(user=self.coach)
        
        url = '/api/plan-cycles/'
        data = {
            'client': self.client_obj.id,
            'start_date': str(date.today() + timedelta(days=10)),
            'end_date': str(date.today() + timedelta(days=17)),
            'cadence': 'weekly',
            'status': 'draft'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_client_cannot_create_plan_cycle(self):
        """Test client cannot create PlanCycle."""
        self.client.force_authenticate(user=self.client_user)
        
        url = '/api/plan-cycles/'
        data = {
            'client': self.client_obj.id,
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=7)),
            'cadence': 'weekly'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_can_view_current_cycle(self):
        """Test client can view their current active cycle."""
        self.client.force_authenticate(user=self.client_user)
        
        url = '/api/client/current-cycle/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.cycle.id)
        self.assertEqual(response.data['status'], 'active')
    
    def test_client_cannot_view_other_client_cycle(self):
        """Test client cannot view another client's cycle."""
        # Create another client and cycle
        other_client_user = User.objects.create_user(
            username='other_client',
            email='other@test.com',
            password='testpass',
            role='client'
        )
        other_client = Client.objects.create(
            first_name='Other',
            last_name='Client',
            email='other@test.com',
            date_of_birth=date(1990, 1, 1),
            sex='F',
            height_cm=165.0,
            initial_weight_kg=65.0,
            user=other_client_user
        )
        other_cycle = PlanCycle.objects.create(
            client=other_client,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            status=PlanCycle.Status.ACTIVE
        )
        
        # Try to access other client's cycle
        self.client.force_authenticate(user=self.client_user)
        url = '/api/client/current-cycle/'
        response = self.client.get(url)
        
        # Should return own cycle, not other client's
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.cycle.id)
        self.assertNotEqual(response.data['id'], other_cycle.id)
    
    def test_coach_can_list_plan_cycles(self):
        """Test coach can list PlanCycles."""
        self.client.force_authenticate(user=self.coach)
        
        url = '/api/plan-cycles/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_coach_can_filter_cycles_by_client(self):
        """Test coach can filter cycles by client."""
        self.client.force_authenticate(user=self.coach)
        
        url = f'/api/plan-cycles/?client={self.client_obj.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for cycle in response.data['results']:
            self.assertEqual(cycle['client'], self.client_obj.id)
