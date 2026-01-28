from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Food

User = get_user_model()


class FoodAPITest(TestCase):
    """Test Food API endpoints and permissions."""
    
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
    
    def test_coach_can_create_food(self):
        """Test that coach can create a food."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'name': 'Chicken Breast',
            'brand': '',
            'nutritional_group': 'carnes_legumbres_huevos',
            'origin_classification': 'animal',
            'serving_size': 100.0,
            'calories_kcal': 165.0,
            'protein_g': 31.0,
            'carbs_g': 0.0,
            'fats_g': 3.6,
        }
        
        response = self.client.post('/api/foods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Food.objects.count(), 1)
        self.assertEqual(Food.objects.first().name, 'Chicken Breast')
    
    def test_client_cannot_create_food(self):
        """Test that client cannot create a food."""
        self.client.force_authenticate(user=self.client_user)
        
        data = {
            'name': 'Test Food',
            'nutritional_group': 'frutas_verduras',
            'origin_classification': 'vegetal',
            'calories_kcal': 50.0,
            'protein_g': 1.0,
            'carbs_g': 10.0,
            'fats_g': 0.5,
        }
        
        response = self.client.post('/api/foods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_can_get_foods_list(self):
        """Test that client can read foods list."""
        # Create a food first
        Food.objects.create(
            name='Test Food',
            nutritional_group=Food.NutritionalGroup.FRUTAS_VERDURAS,
            origin_classification=Food.OriginClassification.VEGETAL,
            calories_kcal=50.0,
            protein_g=1.0,
            carbs_g=10.0,
            fats_g=0.5,
        )
        
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/foods/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', response.data)), 1)
    
    def test_validation_rejects_negative_macros(self):
        """Test that validation rejects negative macro values."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'name': 'Invalid Food',
            'nutritional_group': 'frutas_verduras',
            'origin_classification': 'vegetal',
            'calories_kcal': -10.0,  # Negative value
            'protein_g': 1.0,
            'carbs_g': 10.0,
            'fats_g': 0.5,
        }
        
        response = self.client.post('/api/foods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('calories_kcal', str(response.data))
    
    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        self.client.force_authenticate(user=self.coach)
        
        # Missing required fields
        data = {
            'name': 'Incomplete Food',
            # Missing nutritional_group, origin_classification, macros
        }
        
        response = self.client.post('/api/foods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_coach_can_update_food(self):
        """Test that coach can update a food."""
        food = Food.objects.create(
            name='Original Name',
            nutritional_group=Food.NutritionalGroup.FRUTAS_VERDURAS,
            origin_classification=Food.OriginClassification.VEGETAL,
            calories_kcal=50.0,
            protein_g=1.0,
            carbs_g=10.0,
            fats_g=0.5,
        )
        
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'name': 'Updated Name',
            'nutritional_group': 'frutas_verduras',
            'origin_classification': 'vegetal',
            'calories_kcal': 55.0,
            'protein_g': 1.2,
            'carbs_g': 11.0,
            'fats_g': 0.6,
        }
        
        response = self.client.patch(f'/api/foods/{food.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        food.refresh_from_db()
        self.assertEqual(food.name, 'Updated Name')
