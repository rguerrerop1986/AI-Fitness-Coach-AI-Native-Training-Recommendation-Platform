from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Client(models.Model):
    """Client model for storing client information."""
    
    class Sex(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex.choices)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    height_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(100), MaxValueValidator(250)]
    )
    initial_weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)]
    )
    notes = models.TextField(blank=True)
    consent_checkbox = models.BooleanField(default=False)
    emergency_contact = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_clients',
    )
    deactivation_reason = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
        help_text="Linked User account for client portal access"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Measurement(models.Model):
    """Client body measurements model."""
    
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='measurements'
    )
    date = models.DateField()
    weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)]
    )
    body_fat_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    chest_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    waist_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    hips_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    bicep_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(100)]
    )
    thigh_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)]
    )
    calf_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'measurements'
        ordering = ['-date']
        unique_together = ['client', 'date']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.date} ({self.weight_kg}kg)"
