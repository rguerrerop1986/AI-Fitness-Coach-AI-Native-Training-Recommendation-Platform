from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from decimal import Decimal

User = get_user_model()


class Appointment(models.Model):
    """Appointment model for scheduling consultations with payment tracking."""
    
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'
    
    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash'
        TRANSFER = 'transfer', 'Bank Transfer'
        CARD = 'card', 'Card'
        OTHER = 'other', 'Other'
    
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coach_appointments',
        limit_choices_to={'role': 'coach'}
    )
    scheduled_at = models.DateTimeField(help_text="Scheduled date and time for the appointment")
    duration_minutes = models.IntegerField(
        default=60,
        validators=[MinValueValidator(15)],
        help_text="Duration in minutes (minimum 15)"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    notes = models.TextField(blank=True, help_text="Optional notes about the appointment")
    
    # Payment fields
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price for this consultation (required)"
    )
    currency = models.CharField(max_length=3, default='MXN', help_text="Currency code (e.g., MXN, USD)")
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        blank=True,
        null=True,
        help_text="Payment method used (if paid)"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when payment was recorded"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['client', 'scheduled_at']),
            models.Index(fields=['coach', 'scheduled_at']),
            models.Index(fields=['status', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.client.full_name} - {self.scheduled_at.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"
    
    def clean(self):
        """Validate business rules."""
        from django.core.exceptions import ValidationError
        
        # Only COMPLETED appointments can be marked PAID
        if self.payment_status == self.PaymentStatus.PAID and self.status != self.Status.COMPLETED:
            raise ValidationError({
                'payment_status': 'Appointment must be COMPLETED before marking as PAID.'
            })
        
        # If marked as PAID, require payment_method
        if self.payment_status == self.PaymentStatus.PAID and not self.payment_method:
            raise ValidationError({
                'payment_method': 'Payment method is required when payment status is PAID.'
            })
        
        # If marked as PAID, set paid_at if not already set
        if self.payment_status == self.PaymentStatus.PAID and not self.paid_at:
            from django.utils import timezone
            self.paid_at = timezone.now()
    
    def save(self, *args, **kwargs):
        """Override save to run clean() validation."""
        self.full_clean()
        super().save(*args, **kwargs)
