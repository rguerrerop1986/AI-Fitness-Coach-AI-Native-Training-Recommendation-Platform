from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.clients.models import Client
from .models import Appointment

User = get_user_model()


class AppointmentModelTest(TestCase):
    """Test Appointment model business rules."""
    
    def setUp(self):
        """Set up test data."""
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
        self.client = Client.objects.create(
            first_name='Raul',
            last_name='Client',
            email='raul@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            user=self.client_user
        )
    
    def test_appointment_creation(self):
        """Test creating an appointment."""
        appointment = Appointment.objects.create(
            client=self.client,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            price=500.00,
            currency='MXN'
        )
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.UNPAID)
        self.assertEqual(appointment.price, 500.00)
    
    def test_cannot_mark_paid_before_completed(self):
        """Test that appointment cannot be marked PAID before COMPLETED."""
        appointment = Appointment.objects.create(
            client=self.client,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            price=500.00,
            currency='MXN',
            status=Appointment.Status.SCHEDULED
        )
        
        # Try to mark as PAID while still SCHEDULED
        appointment.payment_status = Appointment.PaymentStatus.PAID
        with self.assertRaises(Exception):  # Should raise ValidationError
            appointment.full_clean()
    
    def test_can_mark_paid_after_completed(self):
        """Test that appointment can be marked PAID after COMPLETED."""
        appointment = Appointment.objects.create(
            client=self.client,
            coach=self.coach,
            scheduled_at=timezone.now() - timedelta(days=1),
            price=500.00,
            currency='MXN',
            status=Appointment.Status.COMPLETED
        )
        
        # Mark as PAID after COMPLETED
        appointment.payment_status = Appointment.PaymentStatus.PAID
        appointment.payment_method = Appointment.PaymentMethod.CASH
        appointment.full_clean()  # Should not raise
        appointment.save()
        
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)
        self.assertIsNotNone(appointment.paid_at)


class AppointmentAPITest(TestCase):
    """Test Appointment API endpoints."""
    
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
        
        self.other_client_user = User.objects.create_user(
            username='other_client',
            email='other@test.com',
            password='testpass123',
            role='client',
            first_name='Other',
            last_name='Client'
        )
        
        self.other_client = Client.objects.create(
            first_name='Other',
            last_name='Client',
            email='other@test.com',
            date_of_birth='1990-01-01',
            sex='M',
            height_cm=175.0,
            initial_weight_kg=80.0,
            user=self.other_client_user
        )
    
    def test_coach_can_create_appointment(self):
        """Test that coach can create an appointment."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'client': self.client_obj.id,
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'duration_minutes': 60,
            'price': 500.00,
            'currency': 'MXN',
            'notes': 'Initial consultation'
        }
        
        response = self.client.post('/api/appointments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(response.data['coach'], self.coach.id)
    
    def test_client_sees_only_own_appointments(self):
        """Test that client can only see their own appointments."""
        # Create appointments for both clients
        appointment1 = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            price=500.00,
            currency='MXN'
        )
        appointment2 = Appointment.objects.create(
            client=self.other_client,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=2),
            price=500.00,
            currency='MXN'
        )
        
        # Client should only see their own appointment
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/client/me/appointments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['all']), 1)
        self.assertEqual(response.data['all'][0]['id'], appointment1.id)
    
    def test_client_cannot_update_appointment(self):
        """Test that client cannot update appointment."""
        appointment = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            price=500.00,
            currency='MXN'
        )
        
        self.client.force_authenticate(user=self.client_user)
        
        # Try to update via coach endpoint (should fail - no access)
        response = self.client.patch(
            f'/api/appointments/{appointment.id}/',
            {'notes': 'Updated notes'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_coach_cannot_mark_paid_before_completed(self):
        """Test that coach cannot mark appointment as PAID before COMPLETED."""
        appointment = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() + timedelta(days=1),
            price=500.00,
            currency='MXN',
            status=Appointment.Status.SCHEDULED
        )
        
        self.client.force_authenticate(user=self.coach)
        
        response = self.client.patch(
            f'/api/appointments/{appointment.id}/mark_paid/',
            {'payment_method': 'cash'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('COMPLETED', response.data['error'])
    
    def test_coach_can_mark_paid_after_completed(self):
        """Test that coach can mark appointment as PAID after COMPLETED."""
        appointment = Appointment.objects.create(
            client=self.client_obj,
            coach=self.coach,
            scheduled_at=timezone.now() - timedelta(days=1),
            price=500.00,
            currency='MXN',
            status=Appointment.Status.COMPLETED
        )
        
        self.client.force_authenticate(user=self.coach)
        
        response = self.client.patch(
            f'/api/appointments/{appointment.id}/mark_paid/',
            {'payment_method': 'cash'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)
        self.assertEqual(appointment.payment_method, Appointment.PaymentMethod.CASH)
        self.assertIsNotNone(appointment.paid_at)
    
    def test_appointment_defaults_to_unpaid(self):
        """Test that new appointments default to UNPAID."""
        self.client.force_authenticate(user=self.coach)
        
        data = {
            'client': self.client_obj.id,
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'duration_minutes': 60,
            'price': 500.00,
            'currency': 'MXN'
        }
        
        response = self.client.post('/api/appointments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['payment_status'], Appointment.PaymentStatus.UNPAID)
