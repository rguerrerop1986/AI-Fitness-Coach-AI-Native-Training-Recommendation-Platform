from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from apps.clients.models import Client
from apps.catalogs.models import Food, Exercise

User = get_user_model()


class DietPlan(models.Model):
    """Diet plan model with versioning support."""
    
    class Goal(models.TextChoices):
        CUT = 'cut', 'Cut (Weight Loss)'
        BULK = 'bulk', 'Bulk (Muscle Gain)'
        MAINTAIN = 'maintain', 'Maintain'
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=10, choices=Goal.choices)
    daily_calories = models.IntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(5000)]
    )
    protein_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        help_text="Protein percentage of total calories"
    )
    carbs_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(20), MaxValueValidator(70)],
        help_text="Carbohydrates percentage of total calories"
    )
    fat_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
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
        return f"{self.title} v{self.version} ({self.get_goal_display()})"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            # Get the highest version for this title
            max_version = DietPlan.objects.filter(title=self.title).aggregate(
                models.Max('version')
            )['version__max'] or 0
            self.version = max_version + 1
        super().save(*args, **kwargs)


class Meal(models.Model):
    """Meal model within a diet plan."""
    
    class MealType(models.TextChoices):
        BREAKFAST = 'breakfast', 'Breakfast'
        LUNCH = 'lunch', 'Lunch'
        DINNER = 'dinner', 'Dinner'
        SNACK = 'snack', 'Snack'
    
    diet_plan = models.ForeignKey(
        DietPlan, 
        on_delete=models.CASCADE, 
        related_name='meals'
    )
    meal_type = models.CharField(max_length=10, choices=MealType.choices)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'meals'
        ordering = ['order']
        unique_together = ['diet_plan', 'meal_type', 'order']
    
    def __str__(self):
        return f"{self.diet_plan.title} - {self.get_meal_type_display()}: {self.name}"


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
    
    title = models.CharField(max_length=200)
    goal = models.CharField(max_length=15, choices=Goal.choices)
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
        return f"{self.title} v{self.version} ({self.get_goal_display()})"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
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
