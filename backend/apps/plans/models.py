from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.clients.models import Client
from apps.catalogs.models import Food, Exercise

User = get_user_model()


class PlanCycle(models.Model):
    """
    Period container for plans and tracking.
    Represents a time-bound cycle (weekly/biweekly/monthly) for a client's fitness journey.
    """
    
    class Cadence(models.TextChoices):
        WEEKLY = 'weekly', 'Weekly'
        BIWEEKLY = 'biweekly', 'Biweekly'
        MONTHLY = 'monthly', 'Monthly'
    
    class Goal(models.TextChoices):
        FAT_LOSS = 'fat_loss', 'Fat Loss'
        RECOMP = 'recomp', 'Recomposition'
        MUSCLE_GAIN = 'muscle_gain', 'Muscle Gain'
        MAINTENANCE = 'maintenance', 'Maintenance'
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SAVED = 'saved', 'Saved'
        PUBLISHED = 'published', 'Published'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='plan_cycles'
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_plan_cycles',
        limit_choices_to={'role': 'coach'}
    )
    start_date = models.DateField()
    end_date = models.DateField()
    cadence = models.CharField(
        max_length=10,
        choices=Cadence.choices,
        default=Cadence.WEEKLY
    )
    goal = models.CharField(
        max_length=15,
        choices=Goal.choices,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT
    )
    notes = models.TextField(blank=True, help_text="Internal notes for the coach")
    plan_pdf = models.FileField(
        upload_to='plan_pdfs/',
        null=True,
        blank=True,
        help_text="Generated PDF of the complete plan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plan_cycles'
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['client', 'start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.client.full_name} - {self.get_cadence_display()} Cycle ({self.start_date} to {self.end_date})"
    
    def clean(self):
        """Validate business rules."""
        errors = {}
        
        # End date must be after start date
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            errors['end_date'] = 'End date must be after start date.'
        
        # Check for overlapping ACTIVE cycles for the same client
        if self.status == self.Status.ACTIVE and self.pk is None:  # New instance
            from django.db.models import Q
            overlapping = PlanCycle.objects.filter(
                client=self.client,
                status=self.Status.ACTIVE
            ).filter(
                Q(start_date__lte=self.end_date) & Q(end_date__gte=self.start_date)
            )
            
            if overlapping.exists():
                errors['status'] = (
                    f'Cannot create active cycle: client already has an active cycle '
                    f'({overlapping.first().start_date} to {overlapping.first().end_date}). '
                    f'Complete or cancel the existing cycle first.'
                )
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if cycle is currently active."""
        from django.utils import timezone
        today = timezone.now().date()
        return (
            self.status == self.Status.ACTIVE and
            self.start_date <= today <= self.end_date
        )
    
    @property
    def duration_days(self):
        """Calculate duration in days."""
        if self.end_date and self.start_date:
            return (self.end_date - self.start_date).days + 1
        return 0


class DietPlan(models.Model):
    """Diet plan model with versioning support."""
    
    class Goal(models.TextChoices):
        CUT = 'cut', 'Cut (Weight Loss)'
        BULK = 'bulk', 'Bulk (Muscle Gain)'
        MAINTAIN = 'maintain', 'Maintain'
    
    plan_cycle = models.OneToOneField(
        PlanCycle,
        on_delete=models.CASCADE,
        related_name='diet_plan',
        null=True,
        blank=True,
        help_text="Link to PlanCycle (one diet plan per cycle)"
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=10, choices=Goal.choices, blank=True)
    daily_calories = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(5000)]
    )
    protein_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Protein percentage of total calories"
    )
    carbs_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(70)],
        help_text="Carbohydrates percentage of total calories"
    )
    fat_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Fat percentage of total calories"
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diet_plans'
        ordering = ['-created_at']
        unique_together = ['title', 'version']
    
    def __str__(self):
        if self.plan_cycle:
            return f"Diet Plan for {self.plan_cycle.client.full_name} ({self.plan_cycle.start_date} to {self.plan_cycle.end_date})"
        return f"{self.title} v{self.version} ({self.get_goal_display() if self.goal else 'N/A'})"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            if self.title:
                # Get the highest version for this title
                max_version = DietPlan.objects.filter(title=self.title).aggregate(
                    models.Max('version')
                )['version__max'] or 0
                self.version = max_version + 1
        super().save(*args, **kwargs)


class Meal(models.Model):
    """Meal model within a diet plan."""
    
    class MealType(models.TextChoices):
        BREAKFAST = 'breakfast', 'Desayuno'
        PRE_WORKOUT = 'pre_workout', 'Pre-entreno'
        POST_WORKOUT = 'post_workout', 'Post-entreno'
        DINNER = 'dinner', 'Cena'
        SNACK = 'snack', 'Snack'
    
    diet_plan = models.ForeignKey(
        DietPlan, 
        on_delete=models.CASCADE, 
        related_name='meals'
    )
    meal_type = models.CharField(max_length=15, choices=MealType.choices)
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Free-text meal description (e.g., 'pan tostado con aguacate...')"
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'meals'
        ordering = ['order', 'meal_type']
        unique_together = ['diet_plan', 'meal_type', 'order']
    
    def __str__(self):
        plan_name = self.diet_plan.title or f"Plan {self.diet_plan.id}"
        return f"{plan_name} - {self.get_meal_type_display()}: {self.name or self.description[:50]}"


class MealItem(models.Model):
    """Food item within a meal."""
    
    meal = models.ForeignKey(
        Meal, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(0.1)],
        help_text="Quantity in grams or milliliters"
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'meal_items'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.food.name} ({self.quantity}g) - {self.meal.name}"
    
    @property
    def total_calories(self):
        return (self.food.kcal * self.quantity) / self.food.serving_size
    
    @property
    def total_protein(self):
        return (self.food.protein_g * self.quantity) / self.food.serving_size
    
    @property
    def total_carbs(self):
        return (self.food.carbs_g * self.quantity) / self.food.serving_size
    
    @property
    def total_fat(self):
        return (self.food.fat_g * self.quantity) / self.food.serving_size


class WorkoutPlan(models.Model):
    """Workout plan model with versioning support."""
    
    class Goal(models.TextChoices):
        STRENGTH = 'strength', 'Strength'
        HYPERTROPHY = 'hypertrophy', 'Muscle Growth'
        ENDURANCE = 'endurance', 'Endurance'
        WEIGHT_LOSS = 'weight_loss', 'Weight Loss'
        GENERAL = 'general', 'General Fitness'
    
    plan_cycle = models.OneToOneField(
        PlanCycle,
        on_delete=models.CASCADE,
        related_name='workout_plan',
        null=True,
        blank=True,
        help_text="Link to PlanCycle (one workout plan per cycle)"
    )
    title = models.CharField(max_length=200, blank=True)
    goal = models.CharField(max_length=15, choices=Goal.choices, blank=True)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_plans'
        ordering = ['-created_at']
        unique_together = ['title', 'version']
    
    def __str__(self):
        if self.plan_cycle:
            return f"Workout Plan for {self.plan_cycle.client.full_name} ({self.plan_cycle.start_date} to {self.plan_cycle.end_date})"
        return f"{self.title} v{self.version} ({self.get_goal_display() if self.goal else 'N/A'})"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            if self.title:
                # Get the highest version for this title
                max_version = WorkoutPlan.objects.filter(title=self.title).aggregate(
                    models.Max('version')
                )['version__max'] or 0
                self.version = max_version + 1
        super().save(*args, **kwargs)


class WorkoutDay(models.Model):
    """Workout day within a workout plan."""
    
    class DayOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'
    
    workout_plan = models.ForeignKey(
        WorkoutPlan, 
        on_delete=models.CASCADE, 
        related_name='workout_days'
    )
    day_of_week = models.CharField(max_length=10, choices=DayOfWeek.choices)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'workout_days'
        ordering = ['order']
        unique_together = ['workout_plan', 'day_of_week']
    
    def __str__(self):
        return f"{self.workout_plan.title} - {self.get_day_of_week_display()}: {self.name}"


class ExerciseSet(models.Model):
    """Exercise set within a workout day."""
    
    class SetType(models.TextChoices):
        REPS = 'reps', 'Repetitions'
        TIME = 'time', 'Time (seconds)'
        DURATION = 'duration', 'Duration (minutes)'
    
    workout_day = models.ForeignKey(
        WorkoutDay, 
        on_delete=models.CASCADE, 
        related_name='exercise_sets'
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    reps_or_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    set_type = models.CharField(max_length=10, choices=SetType.choices, default=SetType.REPS)
    rest_seconds = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
        help_text="Rest time in seconds"
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'exercise_sets'
        ordering = ['order']
    
    def __str__(self):
        if self.set_type == self.SetType.REPS:
            return f"{self.exercise.name} - {self.sets}x{self.reps_or_time} reps"
        elif self.set_type == self.SetType.TIME:
            return f"{self.exercise.name} - {self.sets}x{self.reps_or_time}s"
        else:
            return f"{self.exercise.name} - {self.sets}x{self.reps_or_time}min"


class PlanAssignment(models.Model):
    """Generic model to assign plans to clients."""
    
    class PlanType(models.TextChoices):
        DIET = 'diet', 'Diet Plan'
        WORKOUT = 'workout', 'Workout Plan'
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=10, choices=PlanType.choices)
    diet_plan = models.ForeignKey(
        DietPlan, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    workout_plan = models.ForeignKey(
        WorkoutPlan, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_cycle = models.ForeignKey(
        PlanCycle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        help_text="Optional link to PlanCycle for period-based tracking"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'plan_assignments'
        ordering = ['-created_at']
    
    def __str__(self):
        plan_name = self.diet_plan.title if self.diet_plan else self.workout_plan.title
        return f"{self.client.full_name} - {plan_name} ({self.get_plan_type_display()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.plan_type == self.PlanType.DIET and not self.diet_plan:
            raise ValidationError("Diet plan must be selected for diet assignments.")
        
        if self.plan_type == self.PlanType.WORKOUT and not self.workout_plan:
            raise ValidationError("Workout plan must be selected for workout assignments.")
        
        if self.diet_plan and self.workout_plan:
            raise ValidationError("Cannot assign both diet and workout plan in the same assignment.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TrainingEntry(models.Model):
    """
    Training entry model for workout plans.
    Stores per-session/per-exercise prescription with sets, reps, weight, rest, and notes.
    """
    workout_plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name='training_entries',
        help_text="Workout plan this entry belongs to"
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='plan_entries',
        help_text="Exercise for this training entry"
    )
    date = models.DateField(help_text="Date/session for this training entry")
    series = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of sets"
    )
    repetitions = models.CharField(
        max_length=50,
        help_text="Repetitions (e.g., '8-12' or '10')"
    )
    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Weight in kg (optional, for bodyweight exercises leave blank)"
    )
    rest_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Rest time in seconds (optional)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes for this training entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'training_entries'
        ordering = ['date', 'id']
        indexes = [
            models.Index(fields=['workout_plan', 'date']),
            models.Index(fields=['exercise']),
        ]
    
    def __str__(self):
        weight_str = f" @ {self.weight_kg}kg" if self.weight_kg else ""
        rest_str = f" (rest: {self.rest_seconds}s)" if self.rest_seconds else ""
        return f"{self.exercise.name} - {self.series}x{self.repetitions}{weight_str}{rest_str} - {self.date}"
    
    def clean(self):
        """Validate business rules."""
        from django.core.exceptions import ValidationError
        
        if not self.repetitions or not self.repetitions.strip():
            raise ValidationError({
                'repetitions': 'Repetitions field is required.'
            })
        
        if self.weight_kg is not None and self.weight_kg < 0:
            raise ValidationError({
                'weight_kg': 'Weight must be non-negative.'
            })
        
        if self.rest_seconds is not None and self.rest_seconds < 0:
            raise ValidationError({
                'rest_seconds': 'Rest seconds must be non-negative.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
