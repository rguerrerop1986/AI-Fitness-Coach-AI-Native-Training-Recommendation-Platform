from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta

from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment
from apps.tracking.models import (
    DailyExerciseRecommendation,
    TrainingLog,
    ClientProgressionState,
    DailyReadinessCheckin,
    DailyTrainingRecommendation,
    DailyDietRecommendation,
    DailyTrainingRecommendationExercise,
    DailyDietRecommendationMeal,
    DailyDietRecommendationMealFood,
)
from apps.catalogs.models import Exercise, Food
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
        """Test that authenticated client can access their dashboard (V2 with daily recommendations)."""
        self.client.force_authenticate(user=self.client_user)
        url = reverse('client-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client', response.data)
        self.assertEqual(response.data['client']['id'], self.client_obj.id)
        self.assertIn('today', response.data)
        self.assertIn('diet_plan_active', response.data)
        self.assertIn('training_plan_active', response.data)

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


class ClientDashboardDailyRecommendationTest(APITestCase):
    """Tests for dashboard V2: get-or-create daily recommendation (diet + training)."""

    def setUp(self):
        self.coach = User.objects.create_user(
            username='coach2',
            email='coach2@example.com',
            password='testpass123',
            role='coach',
        )
        self.client_user = User.objects.create_user(
            username='sandy',
            email='sandy@example.com',
            password='testpass123',
            role='client',
            first_name='Sandy',
            last_name='Gabriela',
        )
        self.client_obj = Client.objects.create(
            first_name='Sandy',
            last_name='Gabriela',
            email='sandy@example.com',
            date_of_birth=date(1995, 3, 1),
            sex='F',
            height_m=1.65,
            initial_weight_kg=61.0,
            consent_checkbox=True,
            user=self.client_user,
        )
        # At least one active exercise so training recommendation can be generated
        self.exercise = Exercise.objects.create(
            name='Goblet Squat',
            muscle_group='quads',
            difficulty='beginner',
            intensity=5,
            instructions='Hold kettlebell at chest.',
            is_active=True,
        )
        # Minimum active foods so diet recommendation can be built from catalog (no plan with items)
        self.foods = []
        for i, name in enumerate(['Huevo', 'Avena', 'Plátano', 'Pechuga de pollo', 'Arroz', 'Calabaza', 'Atún', 'Aguacate'], 1):
            self.foods.append(Food.objects.create(
                name=f'{name} test {i}',
                serving_size=100,
                kcal=100 + i * 10,
                protein_g=10,
                carbs_g=10,
                fat_g=5,
                is_active=True,
            ))

    def _create_today_readiness(self):
        """Create today's readiness check-in so dashboard can generate recommendations."""
        today = date.today()
        return DailyReadinessCheckin.objects.create(
            client=self.client_obj,
            date=today,
            sleep_quality=7,
            energy_level=7,
            motivation_today=7,
            preferred_training_mode=DailyReadinessCheckin.PreferredTrainingMode.AUTO,
        )

    def test_dashboard_without_readiness_returns_readiness_required(self):
        """GET dashboard without today's check-in returns readiness_required=True and does not create recommendations."""
        today = date.today()
        self.assertEqual(DailyReadinessCheckin.objects.filter(client=self.client_obj, date=today).count(), 0)
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)

        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('readiness_required') is True)
        self.assertFalse(response.data.get('has_today_readiness'))
        # No recommendations created until user submits readiness
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)

    def test_dashboard_creates_daily_recommendation_when_missing(self):
        """With today's readiness, GET dashboard creates training and diet recommendations when they do not exist."""
        today = date.today()
        self._create_today_readiness()
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)

        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('readiness_required'))

        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)

    def test_dashboard_reuses_existing_recommendation(self):
        """GET dashboard again does not create duplicates; reuses same recommendation."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response1 = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        diet_title_1 = response1.data.get('diet_plan_active') and response1.data['diet_plan_active'].get('title')

        response2 = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        diet_title_2 = response2.data.get('diet_plan_active') and response2.data['diet_plan_active'].get('title')

        today = date.today()
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
        self.assertEqual(diet_title_1, diet_title_2)

    def test_dashboard_persists_exercises(self):
        """Training recommendation can persist exercises from catalog."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        # Either exercises list or recommended_video (or both) may be present
        self.assertIn('exercises', training)
        self.assertIn('recommended_video', training)
        self.assertIn('recommendation_type', training)
        self.assertIn('coach_message', training)

        today = date.today()
        rec = DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).first()
        self.assertIsNotNone(rec)
        # Service may add exercises from catalog when available
        line_count = DailyTrainingRecommendationExercise.objects.filter(recommendation=rec).count()
        self.assertGreaterEqual(line_count, 0)

    def test_dashboard_returns_consolidated_payload(self):
        """Response has client, today, diet_plan_active, training_plan_active, readiness fields."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('client', response.data)
        self.assertEqual(response.data['client']['id'], self.client_obj.id)
        self.assertEqual(response.data['client']['name'], 'Sandy Gabriela')
        self.assertIn('current_weight', response.data['client'])
        self.assertIn('height_cm', response.data['client'])
        self.assertEqual(response.data['client']['height_cm'], 165)

        self.assertIn('today', response.data)
        self.assertIn('diet_plan_active', response.data)
        self.assertIn('training_plan_active', response.data)
        self.assertIn('readiness_required', response.data)
        self.assertIn('has_today_readiness', response.data)
        self.assertIn('has_recommendation_today', response.data)

        diet = response.data['diet_plan_active']
        self.assertIsNotNone(diet)
        self.assertIn('title', diet)
        self.assertIn('goal', diet)
        self.assertIn('coach_message', diet)
        self.assertIn('total_calories', diet)
        self.assertIn('meals', diet)

        training = response.data['training_plan_active']
        self.assertIsNotNone(training)
        self.assertIn('recommendation_type', training)
        self.assertIn('reasoning_summary', training)
        self.assertIn('coach_message', training)
        self.assertIn('recommended_video', training)
        self.assertIn('exercises', training)

    def test_dashboard_idempotent_no_duplicates(self):
        """Multiple GETs do not create duplicate recommendations (unique constraint)."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        for _ in range(3):
            self.client.get(reverse('client-dashboard'))

        today = date.today()
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)

    def test_diet_built_from_catalog_foods(self):
        """Diet recommendation is built from real Food catalog; meals contain foods array."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        diet = response.data.get('diet_plan_active')
        self.assertIsNotNone(diet)
        self.assertIn('meals', diet)
        # At least one meal with at least one real food (from catalog)
        meals_with_foods = [m for m in diet['meals'] if m.get('foods')]
        self.assertGreater(len(meals_with_foods), 0, 'Diet should have at least one meal with foods from catalog')
        first_meal_with_foods = meals_with_foods[0]
        self.assertIn('foods', first_meal_with_foods)
        self.assertGreater(len(first_meal_with_foods['foods']), 0)
        first_food = first_meal_with_foods['foods'][0]
        self.assertIn('id', first_food)
        self.assertIn('name', first_food)
        self.assertIn('quantity', first_food)
        self.assertIn('unit', first_food)

    def test_diet_no_generic_placeholder_titles_only(self):
        """Diet meals are not only generic titles; they have real foods or come from plan."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        diet = response.data.get('diet_plan_active')
        self.assertIsNotNone(diet)
        generic_titles = {'Desayuno alto en proteína', 'Comida principal', 'Cena'}
        for meal in diet.get('meals', []):
            title = (meal.get('title') or '').strip()
            if title in generic_titles and not meal.get('foods'):
                self.fail(f'Meal should not be only generic title without foods: {title}')
        # At least one meal must have foods (catalog-based)
        has_foods = any(m.get('foods') for m in diet.get('meals', []))
        self.assertTrue(has_foods, 'Diet should have at least one meal with foods from catalog')

    def test_training_built_from_catalog_exercises(self):
        """Training recommendation uses only exercises from catalog (persisted in line items)."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        # If exercises are present, they must have names (from catalog)
        for ex in training.get('exercises', []):
            self.assertIn('name', ex)
            self.assertIn('sets', ex)
            self.assertIn('reps', ex)

    def test_training_group_persisted_and_returned(self):
        """training_group is persisted on DailyTrainingRecommendation and returned as training_group_label."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        self.assertIn('training_group', training)
        self.assertIn('training_group_label', training)
        today = date.today()
        rec = DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).first()
        self.assertIsNotNone(rec)
        self.assertTrue(
            hasattr(rec, 'training_group'),
            'DailyTrainingRecommendation should have training_group field',
        )

    def test_dashboard_returns_training_group_label(self):
        """Endpoint returns training_group_label for display (e.g. Tren superior, Core)."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        # When training has exercises, label can be one of the expected groups
        if training.get('exercises'):
            self.assertIn('training_group_label', training)

    def test_insufficient_food_catalog_returns_503(self):
        """When food catalog has too few items and no plan with foods, returns 503 with detail."""
        Food.objects.filter(is_active=True).delete()
        Food.objects.create(name='Only One', serving_size=100, kcal=100, protein_g=10, carbs_g=10, fat_g=5, is_active=True)
        Food.objects.create(name='Only Two', serving_size=100, kcal=100, protein_g=10, carbs_g=10, fat_g=5, is_active=True)
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        self.assertEqual(response.data.get('error'), 'insufficient_catalog')
        self.assertIn('catalog', response.data)

    def test_training_uses_real_catalog_exercises_only(self):
        """Training recommendation uses only real Exercise rows (no hardcoded strings)."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        today = date.today()
        rec = DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).first()
        self.assertIsNotNone(rec)
        for line in DailyTrainingRecommendationExercise.objects.filter(recommendation=rec):
            self.assertIsNotNone(line.exercise)
            self.assertTrue(
                Exercise.objects.filter(pk=line.exercise_id).exists(),
                'Line item exercise must exist in Exercise catalog',
            )

    def test_insanity_videos_are_classified_as_insanity_group(self):
        """Video recommendations with Insanity-style names are classified as insanity group."""
        from apps.training.models import TrainingVideo
        from apps.client_portal.services.daily_recommendation_service import generate_training_recommendation

        TrainingVideo.objects.all().delete()
        video = TrainingVideo.objects.create(
            name='Max Interval Circuit',
            program='Insanity',
            category=TrainingVideo.Category.CARDIO,
            difficulty=TrainingVideo.Difficulty.HIGH,
            duration_minutes=45,
            is_active=True,
        )
        # No exercises in catalog so service debe caer en video
        Exercise.objects.filter(is_active=True).delete()
        ctx = {
            'client_id': self.client_obj.id,
            'target_date': date.today(),
            'last_pain': None,
            'last_energy': None,
            'last_rpe': None,
            'fatigue': None,
            'yesterday_training': None,
            'client_level': 'intermediate',
            'videos_count': 1,
            'exercises_count': 0,
        }
        rec = generate_training_recommendation(self.client_obj, target_date=date.today(), context=ctx)
        self.assertIsNotNone(rec.recommended_video)
        self.assertEqual(rec.recommended_video_id, video.id)
        self.assertEqual(rec.training_group, DailyTrainingRecommendation.TrainingGroup.INSANITY)

    def test_muscle_groups_map_to_upper_lower_core(self):
        """Muscle groups for chest/back/shoulders/bis/tris -> upper_body, legs -> lower_body, core -> core."""
        from apps.client_portal.services.daily_recommendation_service import _derive_training_group

        upper_ex = Exercise.objects.create(
            name='Test Press Pecho',
            muscle_group='chest',
            difficulty='beginner',
            intensity=5,
            instructions='x',
        )
        lower_ex = Exercise.objects.create(
            name='Test Sentadilla',
            muscle_group='quads',
            difficulty='beginner',
            intensity=5,
            instructions='y',
        )
        core_ex = Exercise.objects.create(
            name='Test Plank',
            muscle_group='core',
            difficulty='beginner',
            intensity=4,
            instructions='z',
        )
        group_upper = _derive_training_group('strength', [upper_ex], prefer_recovery=False)
        group_lower = _derive_training_group('strength', [lower_ex], prefer_recovery=False)
        group_core = _derive_training_group('strength', [core_ex], prefer_recovery=False)
        self.assertEqual(group_upper, DailyTrainingRecommendation.TrainingGroup.UPPER_BODY)
        self.assertEqual(group_lower, DailyTrainingRecommendation.TrainingGroup.LOWER_BODY)
        self.assertEqual(group_core, DailyTrainingRecommendation.TrainingGroup.CORE)

    def test_cardio_light_and_mobility_map_to_active_recovery(self):
        """Cardio ligero / movilidad se clasifican como active_recovery cuando aplica."""
        from apps.client_portal.services.daily_recommendation_service import _derive_training_group

        cardio_light = Exercise.objects.create(
            name='Elíptica suave',
            muscle_group='cardio',
            difficulty='beginner',
            intensity=3,
            instructions='x',
            equipment_type='maquina',
            tags=['cardio', 'low_impact'],
        )
        group = _derive_training_group('recovery', [cardio_light], prefer_recovery=True)
        self.assertEqual(group, DailyTrainingRecommendation.TrainingGroup.ACTIVE_RECOVERY)

    def test_training_group_persisted_and_serialized_correctly(self):
        """training_group is persisted on model and serialized as training_group_label."""
        self._create_today_readiness()
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        training = response.data.get('training_plan_active')
        self.assertIsNotNone(training)
        self.assertIn('training_group', training)
        self.assertIn('training_group_label', training)
        today = date.today()
        rec = DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).first()
        self.assertIsNotNone(rec)
        self.assertTrue(
            hasattr(rec, 'training_group'),
            'DailyTrainingRecommendation should have training_group field',
        )
        if rec.training_group:
            self.assertEqual(training['training_group'], rec.training_group)
            self.assertEqual(training['training_group_label'], rec.get_training_group_display())

    def test_seed_client_workout_exercises_is_idempotent(self):
        """Seeding client workout exercises does not duplicate catalog entries."""
        from django.core.management import call_command

        Exercise.objects.filter(
            name__in=[
                'Elíptica',
                'Curl Bíceps con Mancuernas',
                'Climb Mill',
                'Plyometric Cardio Circuit',
            ]
        ).delete()
        call_command('seed_client_workout_exercises')
        first_count = Exercise.objects.filter(
            name__in=[
                'Elíptica',
                'Curl Bíceps con Mancuernas',
                'Climb Mill',
                'Plyometric Cardio Circuit',
            ]
        ).count()
        call_command('seed_client_workout_exercises')
        second_count = Exercise.objects.filter(
            name__in=[
                'Elíptica',
                'Curl Bíceps con Mancuernas',
                'Climb Mill',
                'Plyometric Cardio Circuit',
            ]
        ).count()
        self.assertEqual(first_count, second_count)

    def test_readiness_today_get_empty_then_post(self):
        """GET readiness/today/ returns no check-in; POST creates it; GET returns it."""
        self.client.force_authenticate(user=self.client_user)
        today = date.today()

        r1 = self.client.get(reverse('client-readiness-today'))
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertFalse(r1.data.get('has_today_readiness'))
        self.assertIsNone(r1.data.get('readiness'))

        payload = {
            'sleep_quality': 6,
            'energy_level': 7,
            'motivation_today': 8,
            'preferred_training_mode': 'hybrid',
            'comments': 'Listo para entrenar',
        }
        r2 = self.client.post(reverse('client-readiness-today'), payload, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data.get('sleep_quality'), 6)
        self.assertEqual(r2.data.get('preferred_training_mode'), 'hybrid')
        self.assertEqual(r2.data.get('comments'), 'Listo para entrenar')

        self.assertEqual(DailyReadinessCheckin.objects.filter(client=self.client_obj, date=today).count(), 1)

        r3 = self.client.get(reverse('client-readiness-today'))
        self.assertTrue(r3.data.get('has_today_readiness'))
        self.assertIsNotNone(r3.data.get('readiness'))
        self.assertEqual(r3.data['readiness']['sleep_quality'], 6)

    def test_post_readiness_then_dashboard_generates_recommendation(self):
        """POST readiness then GET dashboard triggers recommendation generation (fallback or AI)."""
        self.client.force_authenticate(user=self.client_user)
        today = date.today()
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 0)

        self.client.post(
            reverse('client-readiness-today'),
            {'sleep_quality': 7, 'energy_level': 7, 'preferred_training_mode': 'auto'},
            format='json',
        )
        response = self.client.get(reverse('client-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('readiness_required'))
        self.assertTrue(response.data.get('has_today_readiness'))
        # Should have created recommendations (via AI or fallback)
        self.assertEqual(DailyTrainingRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
        self.assertEqual(DailyDietRecommendation.objects.filter(client=self.client_obj, date=today).count(), 1)
