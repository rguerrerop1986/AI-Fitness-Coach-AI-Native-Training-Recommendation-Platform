"""
Models for the training module: video catalog, daily check-ins, workout logs, and recommendations.
"""
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings


class TrainingVideo(models.Model):
    """Catalog of workout videos/rutinas (e.g. Insanity)."""

    class Category(models.TextChoices):
        CARDIO = 'cardio', 'Cardio'
        RECOVERY = 'recovery', 'Recovery'
        PLYOMETRICS = 'plyometrics', 'Plyometrics'
        CORE = 'core', 'Core'
        STRENGTH = 'strength', 'Strength'
        MIXED = 'mixed', 'Mixed'

    class Difficulty(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        MAX = 'max', 'Max'

    name = models.CharField(max_length=200)
    program = models.CharField(max_length=100, default='Insanity', blank=True)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.MIXED,
    )
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    # Stress / impact flags for rule-based filtering
    stresses_legs = models.BooleanField(default=True)
    stresses_upper_body = models.BooleanField(default=False)
    stresses_core = models.BooleanField(default=True)
    explosive = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'training_videos'
        ordering = ['program', 'name']

    def __str__(self) -> str:
        return f"{self.name} ({self.get_difficulty_display()})"


class DailyCheckIn(models.Model):
    """User's pre-workout state for a given day (one per user per date)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_checkins',
    )
    date = models.DateField(db_index=True)
    # Sleep
    hours_sleep = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )
    sleep_quality = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    # Energy & motivation
    energy_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    motivation_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    mood = models.CharField(max_length=100, blank=True)
    # Soreness (1-10)
    soreness_legs = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    soreness_arms = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    soreness_core = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    soreness_shoulders = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    joint_pain = models.BooleanField(default=False)
    pain_notes = models.TextField(blank=True)
    # Gym context
    did_gym_today = models.BooleanField(default=False)
    did_gym_yesterday = models.BooleanField(default=False)
    gym_focus = models.CharField(max_length=100, blank=True)
    wants_intensity = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_daily_checkins'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'],
                name='training_daily_checkins_user_date_unique',
            ),
        ]
        indexes = [models.Index(fields=['user', 'date'])]

    def __str__(self) -> str:
        return f"{self.user} - {self.date}"


class WorkoutLog(models.Model):
    """Result of the user's workout for a given day (video done + feedback)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_workout_logs',
    )
    date = models.DateField(db_index=True)
    video = models.ForeignKey(
        TrainingVideo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workout_logs',
    )
    completed = models.BooleanField(default=True)
    paused = models.BooleanField(default=False)
    # RPE 1-10
    rpe = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    breathing = models.CharField(max_length=100, blank=True, default="")
    sweat_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    satisfaction = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    performance = models.CharField(max_length=100, blank=True, default="")
    felt_strong = models.BooleanField(null=True, blank=True)
    felt_drained = models.BooleanField(null=True, blank=True)
    recovery_fast = models.BooleanField(null=True, blank=True)
    pain_during_workout = models.BooleanField(default=False)
    pain_notes = models.TextField(blank=True)
    body_feedback = models.TextField(blank=True)
    emotional_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_workout_logs'
        ordering = ['-date']
        indexes = [models.Index(fields=['user', 'date'])]

    def __str__(self) -> str:
        return f"{self.user} - {self.date} ({self.video.name if self.video else 'N/A'})"


class TrainingRecommendation(models.Model):
    """System-generated recommendation for a user on a given date (one per user per date)."""

    class RecommendationType(models.TextChoices):
        RECOVERY = 'recovery', 'Recovery'
        LIGHT = 'light', 'Light'
        MODERATE = 'moderate', 'Moderate'
        INTENSE = 'intense', 'Intense'
        MAX = 'max', 'Max'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_recommendations',
    )
    date = models.DateField(db_index=True)
    recommended_video = models.ForeignKey(
        TrainingVideo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations',
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RecommendationType.choices,
        default=RecommendationType.MODERATE,
    )
    reasoning_summary = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    coach_message = models.TextField(blank=True)
    rule_based_payload = models.JSONField(default=dict, blank=True)
    llm_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_recommendations'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'date'],
                name='training_recommendations_user_date_unique',
            ),
        ]
        indexes = [models.Index(fields=['user', 'date'])]

    def __str__(self) -> str:
        return f"{self.user} - {self.date} ({self.get_recommendation_type_display()})"
