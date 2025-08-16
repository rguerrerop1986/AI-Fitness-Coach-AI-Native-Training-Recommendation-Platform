from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.clients.models import Client

User = get_user_model()


class CheckIn(models.Model):
    """Client check-in model for tracking progress and adherence."""
    
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='checkins'
    )
    date = models.DateField()
    weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)],
        null=True, 
        blank=True
    )
    body_fat_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        null=True, 
        blank=True
    )
    chest_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        null=True, 
        blank=True
    )
    waist_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        null=True, 
        blank=True
    )
    hips_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(50), MaxValueValidator(200)],
        null=True, 
        blank=True
    )
    bicep_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(20), MaxValueValidator(100)],
        null=True, 
        blank=True
    )
    thigh_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(150)],
        null=True, 
        blank=True
    )
    calf_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(20), MaxValueValidator(100)],
        null=True, 
        blank=True
    )
    notes = models.TextField(blank=True)
    rpe = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, 
        blank=True,
        help_text="Rate of Perceived Exertion (1-10 scale)"
    )
    fatigue = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, 
        blank=True,
        help_text="Fatigue level (1-10 scale)"
    )
    diet_adherence = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, 
        blank=True,
        help_text="Diet adherence percentage (0-100)"
    )
    workout_adherence = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, 
        blank=True,
        help_text="Workout adherence percentage (0-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'checkins'
        ordering = ['-date']
        unique_together = ['client', 'date']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.date}"
    
    @property
    def has_measurements(self):
        """Check if check-in has any body measurements."""
        return any([
            self.weight_kg, self.body_fat_pct, self.chest_cm, 
            self.waist_cm, self.hips_cm, self.bicep_cm, 
            self.thigh_cm, self.calf_cm
        ])
    
    @property
    def has_adherence_data(self):
        """Check if check-in has adherence data."""
        return self.diet_adherence is not None or self.workout_adherence is not None
    
    @property
    def has_subjective_data(self):
        """Check if check-in has subjective data (RPE, fatigue)."""
        return self.rpe is not None or self.fatigue is not None
