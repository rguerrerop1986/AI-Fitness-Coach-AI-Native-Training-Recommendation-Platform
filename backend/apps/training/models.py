"""
Models for the training module: video catalog, daily check-ins, workout logs, and recommendations.
"""
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone


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
    url = models.URLField(blank=True, help_text='Optional video URL for client playback')
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
    stress_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    muscle_soreness = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    diet_adherence_yesterday = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    hydration_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    recovery_feeling = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    mental_clarity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    workout_desire = models.PositiveSmallIntegerField(
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
    had_alcohol_yesterday = models.BooleanField(default=False)
    feels_pain_or_injury = models.BooleanField(default=False)
    pain_notes = models.TextField(blank=True)
    # Gym context
    did_gym_today = models.BooleanField(default=False)
    did_gym_yesterday = models.BooleanField(default=False)
    gym_focus = models.CharField(max_length=100, blank=True)
    wants_intensity = models.BooleanField(default=True)
    wants_insanity_today = models.BooleanField(default=False)
    wants_strength_today = models.BooleanField(default=False)
    wants_recovery_today = models.BooleanField(default=False)
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


class WorkoutSession(models.Model):
    """Track a workout session with support for video and gym flows."""

    class WorkoutType(models.TextChoices):
        VIDEO_WORKOUT = "video_workout", "Video Workout"
        GYM_WORKOUT = "gym_workout", "Gym Workout"

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="training_workout_sessions",
    )
    session_date = models.DateField(default=timezone.localdate, db_index=True)
    workout_type = models.CharField(
        max_length=20,
        choices=WorkoutType.choices,
        default=WorkoutType.VIDEO_WORKOUT,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    title = models.CharField(max_length=200, blank=True)
    video_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_exercises = models.PositiveIntegerField(default=0)
    total_sets = models.PositiveIntegerField(default=0)
    total_reps = models.PositiveIntegerField(default=0)
    total_volume = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_workout_sessions"
        ordering = ["-session_date", "-created_at"]
        indexes = [models.Index(fields=["user", "session_date"])]

    def __str__(self) -> str:
        return f"{self.user} - {self.session_date} ({self.workout_type})"


class WorkoutExercise(models.Model):
    """An exercise row inside a gym workout session."""

    workout_session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name="exercises",
    )
    exercise_name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)
    intensity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_workout_exercises"
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["workout_session", "order"])]

    def __str__(self) -> str:
        return f"{self.workout_session_id} - {self.exercise_name}"


class ExerciseSet(models.Model):
    """Set execution details for each workout exercise."""

    workout_exercise = models.ForeignKey(
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name="sets",
    )
    set_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    reps = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    intensity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    rest_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_exercise_sets"
        ordering = ["set_number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["workout_exercise", "set_number"],
                name="training_exercise_sets_exercise_set_number_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.workout_exercise_id} - Set {self.set_number}"


class TrainingRecommendation(models.Model):
    """System-generated recommendation for a user on a given date (one per user per date)."""

    class RecommendationType(models.TextChoices):
        INSANITY_MAX = 'insanity_max', 'Insanity Max'
        INSANITY_MODERATE = 'insanity_moderate', 'Insanity Moderate'
        STRENGTH_UPPER = 'strength_upper', 'Strength Upper'
        STRENGTH_LOWER = 'strength_lower', 'Strength Lower'
        HYBRID_TRAINING = 'hybrid_training', 'Hybrid Training'
        MOBILITY_RECOVERY = 'mobility_recovery', 'Mobility Recovery'
        CARDIO_LIGHT = 'cardio_light', 'Cardio Light'
        FULL_REST = 'full_rest', 'Full Rest'
        RECOVERY = 'recovery', 'Recovery'
        LIGHT = 'light', 'Light'
        MODERATE = 'moderate', 'Moderate'
        INTENSE = 'intense', 'Intense'
        MAX = 'max', 'Max'
        MOBILITY = 'mobility', 'Mobility'
        UPPER_STRENGTH = 'upper_strength', 'Upper Strength'
        LOWER_STRENGTH = 'lower_strength', 'Lower Strength'
        CARDIO = 'cardio', 'Cardio'
        FULL_BODY = 'full_body', 'Full Body'
        REST_DAY = 'rest_day', 'Rest Day'

    class IntensityLevel(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        RECOVERY = "recovery", "Recovery"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='training_recommendations',
    )
    date = models.DateField(db_index=True)
    checkin = models.ForeignKey(
        DailyCheckIn,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations',
    )
    recommended_video = models.ForeignKey(
        TrainingVideo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations',
    )
    recommended_exercise = models.ForeignKey(
        'catalogs.Exercise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_recommendations',
    )
    recommendation_type = models.CharField(
        max_length=24,
        choices=RecommendationType.choices,
        default=RecommendationType.MODERATE,
    )
    reasoning_summary = models.TextField(blank=True)
    warnings = models.JSONField(default=list, blank=True)
    coach_message = models.TextField(blank=True)
    readiness_score = models.FloatField(null=True, blank=True)
    intensity_level = models.CharField(
        max_length=12,
        choices=IntensityLevel.choices,
        default=IntensityLevel.MODERATE,
    )
    duration_minutes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
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


class TrainingRecommendationExercise(models.Model):
    """One exercise within a training recommendation (sets, reps, rest)."""

    recommendation = models.ForeignKey(
        TrainingRecommendation,
        on_delete=models.CASCADE,
        related_name='recommended_exercises',
    )
    exercise = models.ForeignKey(
        'catalogs.Exercise',
        on_delete=models.CASCADE,
        related_name='recommendation_line_items',
    )
    sets = models.PositiveSmallIntegerField(default=0)
    reps = models.PositiveSmallIntegerField(default=0)
    rest_seconds = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'training_recommendation_exercises'
        ordering = ['recommendation', 'position']

    def __str__(self) -> str:
        return f"{self.recommendation} - {self.exercise.name} ({self.sets}x{self.reps})"


class CompletedWorkout(models.Model):
    """Completed workout feedback linked to a generated recommendation."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="completed_workouts",
    )
    recommendation = models.ForeignKey(
        TrainingRecommendation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_workouts",
    )
    date = models.DateField(db_index=True)
    workout_type = models.CharField(max_length=32)
    perceived_exertion = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    energy_after = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    satisfaction = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    completed = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_completed_workouts"
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self) -> str:
        return f"{self.user} - {self.date} ({self.workout_type})"
