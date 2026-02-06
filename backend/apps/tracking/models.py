from decimal import Decimal
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
        SKIPPED = 'skipped', 'Skipped'
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

    # Recommendation engine fields (ML-ready; rules_v1 for MVP)
    recommendation_version = models.CharField(max_length=50, default='rules_v1', blank=True)
    recommendation_meta = models.JSONField(null=True, blank=True)
    recommendation_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

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
        null=True,
        blank=True,
    )
    height_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estatura en metros (ESTRUCTURAL)',
    )
    bmi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Índice de Masa Corporal (calculado: weight_kg / height_m²)',
    )
    rc_termino = models.IntegerField(null=True, blank=True, help_text='Frecuencia cardíaca al término')
    rc_1min_bpm = models.IntegerField(null=True, blank=True, help_text='Frecuencia cardíaca 1 minuto después (API: rc_1min)')
    is_structural = models.BooleanField(default=True, help_text='Check-in tipo ESTRUCTURAL con pliegues/diámetros/perímetros')
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
        blank=True,
    )
    # ---- ESTRUCTURAL: Pliegues (mm): 3 mediciones + promedio ----
    skinfold_triceps_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_triceps_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_triceps_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_triceps_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_subscapular_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_subscapular_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_subscapular_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_subscapular_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_suprailiac_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_suprailiac_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_suprailiac_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_suprailiac_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_abdominal_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_abdominal_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_abdominal_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_abdominal_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_ant_thigh_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_ant_thigh_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_ant_thigh_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_ant_thigh_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_calf_1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_calf_2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_calf_3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    skinfold_calf_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # ---- ESTRUCTURAL: Diámetros (cm): izquierdo, derecho, promedio ----
    diameter_femoral_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_femoral_r = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_femoral_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_humeral_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_humeral_r = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_humeral_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_styloid_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_styloid_r = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diameter_styloid_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # ---- ESTRUCTURAL: Perímetros (cm) ----
    perimeter_waist = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_abdomen = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_calf = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_hip = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_chest = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_arm_relaxed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_arm_flexed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_thigh_relaxed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    perimeter_thigh_flexed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
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
            self.weight_kg,
            self.body_fat_pct,
            self.chest_cm,
            self.waist_cm,
            self.hips_cm,
            self.bicep_cm,
            self.thigh_cm,
            self.calf_cm,
            self.skinfold_triceps_avg,
            self.perimeter_waist,
            self.diameter_femoral_avg,
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
        """Auto-link to active PlanCycle if not set; recalc BMI from weight_kg and height_m."""
        if self.weight_kg is not None and self.height_m is not None:
            try:
                h = float(self.height_m)
                if h > 0:
                    w = float(self.weight_kg)
                    self.bmi = round(Decimal(str(w)) / (Decimal(str(h)) * Decimal(str(h))), 2)
            except (TypeError, ValueError, ZeroDivisionError):
                self.bmi = None
        else:
            self.bmi = None
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
                pass
        super().save(*args, **kwargs)


class DailyExerciseRecommendation(models.Model):
    """
    Persisted daily exercise recommendation for a client (V1 heuristic engine).
    One record per client per date; generated on first GET or by scheduler.
    """
    class Status(models.TextChoices):
        RECOMMENDED = 'recommended', 'Recomendado'
        COMPLETED = 'completed', 'Completado'
        SKIPPED = 'skipped', 'Omitido'

    class Intensity(models.TextChoices):
        LOW = 'low', 'Baja'
        MODERATE = 'moderate', 'Moderada'
        HIGH = 'high', 'Alta'

    class Type(models.TextChoices):
        MOBILITY = 'mobility', 'Movilidad'
        CARDIO = 'cardio', 'Cardio'
        STRENGTH = 'strength', 'Fuerza'
        CORE = 'core', 'Core'
        HIIT = 'hiit', 'HIIT'

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='daily_exercise_recommendations',
    )
    date = models.DateField(db_index=True)
    exercise = models.ForeignKey(
        'catalogs.Exercise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_recommendations',
    )
    intensity = models.CharField(
        max_length=20,
        choices=Intensity.choices,
        default=Intensity.MODERATE,
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.STRENGTH,
    )
    rationale = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECOMMENDED,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_exercise_recommendations'
        ordering = ['-date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'date'], name='daily_ex_rec_client_date_unique'),
        ]
        indexes = [
            models.Index(fields=['client', 'date']),
        ]

    def __str__(self):
        return f'{self.client.full_name} - {self.date} ({self.get_status_display()})'


class ClientProgressionState(models.Model):
    """
    Persistent state for closed-loop recommendation V1.1.
    One record per client; updated after each completed recommendation (TrainingLog outcome).
    """
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='progression_state',
    )
    current_load_score = models.FloatField(default=0.0)
    intensity_bias = models.SmallIntegerField(
        default=0,
        validators=[MinValueValidator(-2), MaxValueValidator(2)],
        help_text='Global intensity adjustment -2 to +2',
    )
    preferred_types = models.JSONField(
        default=dict,
        blank=True,
        help_text='Type weights e.g. {"CARDIO": 0.2, "STRENGTH": 0.1}',
    )
    last_recommended_type = models.CharField(max_length=20, null=True, blank=True)
    high_days_streak = models.PositiveSmallIntegerField(
        default=0,
        help_text='Consecutive days with HIGH intensity (for guardrail: max 2)',
    )
    cooldown_days_remaining = models.PositiveSmallIntegerField(
        default=0,
        help_text='Days to force low intensity after injury_risk (e.g. 3)',
    )
    cooldown_last_tick_date = models.DateField(
        null=True,
        blank=True,
        help_text='Last calendar date when cooldown was ticked (for day-based decrement)',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_progression_states'

    def __str__(self):
        return f'{self.client.full_name} progression (bias={self.intensity_bias})'
