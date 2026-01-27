from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, 'coach')

    def test_user_str_representation(self):
        user = User.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe',
            role='assistant'
        )
        self.assertEqual(str(user), 'John Doe (assistant)')

    def test_user_properties(self):
        coach = User.objects.create_user(username='coach', role='coach')
        assistant = User.objects.create_user(username='assistant', role='assistant')
        
        self.assertTrue(coach.is_coach)
        self.assertFalse(coach.is_assistant)
        self.assertTrue(assistant.is_assistant)
        self.assertFalse(assistant.is_coach)


class UserAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_access(self):
        self.client.force_authenticate(user=self.user)
        url = '/api/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
