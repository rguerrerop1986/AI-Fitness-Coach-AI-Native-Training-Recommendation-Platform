from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.clients.models import Client

User = get_user_model()


class TrainingLog(models.Model):
    """ML-ready daily training log: suggested vs executed, adherence signals."""

    class ExecutionStatus(models.TextChoices):
        NOT_DONE = 'not_done', 'Not Done'
        PARTIAL = 'partial', 'Partial'
        DONE = 'done', 'Done'
        REPLACED = 'replaced', 'Replaced'
        INJURY_STOP = 'injury_stop', 'Injury Stop'
        SICK = 'sick', 'Sick'

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='training_logs',
    )
    plan_cycle = models.ForeignKey(
        'plans.PlanCycle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_logs',
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_logs_reviewed',
    )
    date = models.DateField()

    suggested_exercise = models.ForeignKey(
        'catalogs.Exercise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggested_logs',
    )
    executed_exercise = models.ForeignKey(
        'catalogs.Exercise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_logs',
    )
    execution_status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.NOT_DONE,
    )

    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    rpe = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Rate of Perceived Exertion 1-10',
    )
    energy_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    pain_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'training_logs'
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'date'], name='training_logs_client_date_unique'),
        ]
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['plan_cycle', 'date']),
        ]

    def __str__(self):
        return f'{self.client.full_name} - Training {self.date}'

    def save(self, *args, **kwargs):
        if not self.plan_cycle and self.client and self.date:
            try:
                from apps.plans.models import PlanCycle
                active = PlanCycle.objects.filter(
                    client=self.client,
                    status=PlanCycle.Status.ACTIVE,
                    start_date__lte=self.date,
                    end_date__gte=self.date,
                ).first()
                if active:
                    self.plan_cycle = active
            except Exception:
                pass
        super().save(*args, **kwargs)


class DietLog(models.Model):
    """ML-ready daily diet log: adherence and hunger/craving/digestion signals."""

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='diet_logs',
    )
    plan_cycle = models.ForeignKey(
        'plans.PlanCycle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diet_logs',
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diet_logs_reviewed',
    )
    date = models.DateField()

    adherence_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    calories_estimate_kcal = models.PositiveIntegerField(null=True, blank=True)
    protein_estimate_g = models.PositiveIntegerField(null=True, blank=True)
    carbs_estimate_g = models.PositiveIntegerField(null=True, blank=True)
    fats_estimate_g = models.PositiveIntegerField(null=True, blank=True)

    hunger_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    cravings_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    digestion_quality = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diet_logs'
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'date'], name='diet_logs_client_date_unique'),
        ]
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['plan_cycle', 'date']),
        ]

    def __str__(self):
        return f'{self.client.full_name} - Diet {self.date}'

    def save(self, *args, **kwargs):
        if not self.plan_cycle and self.client and self.date:
            try:
                from apps.plans.models import PlanCycle
                active = PlanCycle.objects.filter(
                    client=self.client,
                    status=PlanCycle.Status.ACTIVE,
                    start_date__lte=self.date,
                    end_date__gte=self.date,
                ).first()
                if active:
                    self.plan_cycle = active
            except Exception:
                pass
        super().save(*args, **kwargs)


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
    plan_cycle = models.ForeignKey(
        'plans.PlanCycle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkins',
        help_text="Optional link to PlanCycle for period-based tracking"
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
    
    def save(self, *args, **kwargs):
        """Auto-link to active PlanCycle if not set."""
        if not self.plan_cycle and self.client and self.date:
            try:
                from apps.plans.models import PlanCycle
                active_cycle = PlanCycle.objects.filter(
                    client=self.client,
                    status=PlanCycle.Status.ACTIVE,
                    start_date__lte=self.date,
                    end_date__gte=self.date
                ).first()
                
                if active_cycle:
                    self.plan_cycle = active_cycle
            except Exception:
                # If PlanCycle doesn't exist yet (during migrations), skip
                pass
        
        super().save(*args, **kwargs)
