from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from apps.catalogs.models import Exercise
from .models import WorkoutPlan, TrainingEntry, PlanAssignment

User = get_user_model()


class TrainingEntryAPITest(TestCase):
    """Test TrainingEntry API endpoints and permissions."""
    
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
        
        self.other_client = Client.objects.create(
            first_name='Other',
            last_name='Client',
            email='other@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
        )
        
        self.exercise = Exercise.objects.create(
            name='Bench Press',
            muscle_group=Exercise.MuscleGroup.CHEST,
            equipment_type=Exercise.EquipmentType.BARRA,
            instructions='Lie on bench, press bar',
        )
        
        self.workout_plan = WorkoutPlan.objects.create(
            title='Strength Program',
            goal=WorkoutPlan.Goal.STRENGTH,
            created_by=self.coach
        )
        
        # Assign workout plan to client
        self.assignment = PlanAssignment.objects.create(
            client=self.client_obj,
            plan_type=PlanAssignment.PlanType.WORKOUT,
            workout_plan=self.workout_plan,
            start_date=date.today(),
            assigned_by=self.coach
        )
    
    def test_coach_can_add_training_entry(self):
        """Test that coach can add training entry to workout plan."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'workout_plan': self.workout_plan.id,
            'exercise': self.exercise.id,
            'date': date.today().isoformat(),
            'series': 3,
            'repetitions': '8-12',
            'weight_kg': 60.0,
            'rest_seconds': 90,
            'notes': 'Focus on form',
        }
        
        response = self.client.post('/api/training-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrainingEntry.objects.count(), 1)
        entry = TrainingEntry.objects.first()
        self.assertEqual(entry.exercise, self.exercise)
        self.assertEqual(entry.series, 3)
    
    def test_client_can_read_own_plan_entries(self):
        """Test that client can read entries from their assigned plans."""
        # Create entry
        entry = TrainingEntry.objects.create(
            workout_plan=self.workout_plan,
            exercise=self.exercise,
            date=date.today(),
            series=3,
            repetitions='10',
            weight_kg=60.0,
        )
        
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/training-entries/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['id'], entry.id)
    
    def test_client_cannot_read_other_client_entries(self):
        """Test that client cannot read entries from other clients' plans."""
        # Create workout plan for other client
        other_plan = WorkoutPlan.objects.create(
            title='Other Plan',
            goal=WorkoutPlan.Goal.STRENGTH,
            created_by=self.coach
        )
        
        PlanAssignment.objects.create(
            client=self.other_client,
            plan_type=PlanAssignment.PlanType.WORKOUT,
            workout_plan=other_plan,
            start_date=date.today(),
            assigned_by=self.coach
        )
        
        # Create entry for other client's plan
        TrainingEntry.objects.create(
            workout_plan=other_plan,
            exercise=self.exercise,
            date=date.today(),
            series=3,
            repetitions='10',
        )
        
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/training-entries/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        # Should only see own entries (none in this case)
        self.assertEqual(len(results), 0)
    
    def test_client_cannot_create_training_entry(self):
        """Test that client cannot create training entries."""
        self.client.force_authenticate(user=self.client_user)
        
        data = {
            'workout_plan': self.workout_plan.id,
            'exercise': self.exercise.id,
            'date': date.today().isoformat(),
            'series': 3,
            'repetitions': '10',
        }
        
        response = self.client.post('/api/training-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_validation_requires_repetitions(self):
        """Test that repetitions field is required."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'workout_plan': self.workout_plan.id,
            'exercise': self.exercise.id,
            'date': date.today().isoformat(),
            'series': 3,
            # Missing repetitions
        }
        
        response = self.client.post('/api/training-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repetitions', str(response.data))
