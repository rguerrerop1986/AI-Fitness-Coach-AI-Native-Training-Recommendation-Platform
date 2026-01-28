from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from apps.catalogs.models import Exercise
from .models import WorkoutPlan, TrainingEntry, PlanCycle, DietPlan, Meal

User = get_user_model()


class PlanCycleAPITest(TestCase):
    """Test PlanCycle API endpoints and PDF generation."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.coach = User.objects.create_user(
            username='coach',
            email='coach@test.com',
            password='testpass123',
            role='coach',
            first_name='Coach',
            last_name='Test'
        )
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='testpass123',
            role='client',
            first_name='Client',
            last_name='Test'
        )
        
        self.client_obj = Client.objects.create(
            first_name='Raul',
            last_name='Client',
            email='raul@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            user=self.client_user
        )
    
    def test_coach_can_create_cycle_with_period_days(self):
        """Test that coach can create a cycle with period_days helper."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'client': self.client_obj.id,
            'period_days': 15,
            'goal': 'fat_loss',
            'status': 'draft',
        }
        
        response = self.client.post('/api/plan-cycles/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlanCycle.objects.count(), 1)
        
        cycle = PlanCycle.objects.first()
        self.assertEqual(cycle.duration_days, 15)
        self.assertEqual(cycle.client, self.client_obj)
        self.assertEqual(cycle.coach, self.coach)
    
    def test_coach_can_create_diet_plan(self):
        """Test that coach can create a diet plan for a cycle."""
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
        )
        
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'title': 'Test Diet Plan',
        }
        
        response = self.client.post(f'/api/plan-cycles/{cycle.id}/diet-plan/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        cycle.refresh_from_db()
        self.assertIsNotNone(cycle.diet_plan)
    
    def test_coach_can_add_meal_to_diet_plan(self):
        """Test that coach can add meals to a diet plan."""
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
        )
        
        diet_plan = DietPlan.objects.create(
            plan_cycle=cycle,
            created_by=self.coach,
        )
        
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'meal_type': 'breakfast',
            'description': 'Pan tostado con aguacate',
            'order': 0,
        }
        
        response = self.client.post(f'/api/plan-cycles/{cycle.id}/diet-plan/meals/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meal.objects.count(), 1)
        
        meal = Meal.objects.first()
        self.assertEqual(meal.meal_type, 'breakfast')
        self.assertEqual(meal.description, 'Pan tostado con aguacate')
    
    def test_coach_can_generate_pdf(self):
        """Test that coach can generate PDF for a plan cycle."""
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
        )
        
        self.client.force_authenticate(user=self.coach)
        
        response = self.client.post(f'/api/plan-cycles/{cycle.id}/generate-pdf/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        cycle.refresh_from_db()
        self.assertIsNotNone(cycle.plan_pdf)
    
    def test_client_can_download_own_pdf(self):
        """Test that client can download PDF for their own cycle."""
        cycle = PlanCycle.objects.create(
            client=self.client_obj,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            status=PlanCycle.Status.ACTIVE,
        )
        
        # Generate PDF first
        from .services.pdf_service import generate_plan_pdf
        from django.core.files.base import ContentFile
        pdf_buffer = generate_plan_pdf(cycle)
        cycle.plan_pdf.save('test_plan.pdf', ContentFile(pdf_buffer.read()), save=True)
        
        self.client.force_authenticate(user=self.client_user)
        
        response = self.client.get('/api/client/current-plan/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_client_cannot_download_other_client_pdf(self):
        """Test that client cannot download PDF for another client's cycle."""
        other_client = Client.objects.create(
            first_name='Other',
            last_name='Client',
            email='other@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
        )
        
        cycle = PlanCycle.objects.create(
            client=other_client,
            coach=self.coach,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            status=PlanCycle.Status.ACTIVE,
        )
        
        from .services.pdf_service import generate_plan_pdf
        from django.core.files.base import ContentFile
        pdf_buffer = generate_plan_pdf(cycle)
        cycle.plan_pdf.save('test_plan.pdf', ContentFile(pdf_buffer.read()), save=True)
        
        self.client.force_authenticate(user=self.client_user)
        
        # Try to access other client's PDF via direct URL (should fail)
        response = self.client.get(f'/api/plans/plan-cycles/{cycle.id}/download-pdf/')
        # Should be 403 or 404 depending on permissions
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
