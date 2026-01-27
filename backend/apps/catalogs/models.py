from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Food(models.Model):
    """Food catalog model with nutritional information."""
    
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    serving_size = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(0.1)],
        help_text="Serving size in grams or milliliters"
    )
    kcal = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        help_text="Calories per serving"
    )
    protein_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        help_text="Protein in grams per serving"
    )
    carbs_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        help_text="Carbohydrates in grams per serving"
    )
    fat_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        help_text="Fat in grams per serving"
    )
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for categorization")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'foods'
        ordering = ['name']
        unique_together = ['name', 'brand']
    
    def __str__(self):
        if self.brand:
            return f"{self.name} ({self.brand})"
        return self.name
    
    @property
    def full_name(self):
        if self.brand:
            return f"{self.name} - {self.brand}"
        return self.name


class Exercise(models.Model):
    """Exercise catalog model with workout information."""
    
    class MuscleGroup(models.TextChoices):
        CHEST = 'chest', 'Chest'
        BACK = 'back', 'Back'
        SHOULDERS = 'shoulders', 'Shoulders'
        BICEPS = 'biceps', 'Biceps'
        TRICEPS = 'triceps', 'Triceps'
        FOREARMS = 'forearms', 'Forearms'
        CORE = 'core', 'Core'
        QUADS = 'quads', 'Quadriceps'
        HAMSTRINGS = 'hamstrings', 'Hamstrings'
        GLUTES = 'glutes', 'Glutes'
        CALVES = 'calves', 'Calves'
        CARDIO = 'cardio', 'Cardio'
        FULL_BODY = 'full_body', 'Full Body'
        OTHER = 'other', 'Other'
    
    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
    
    name = models.CharField(max_length=200)
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices)
    equipment = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=15, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    instructions = models.TextField()
    video_url = models.URLField(blank=True, help_text="Optional video demonstration URL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exercises'
        ordering = ['muscle_group', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_muscle_group_display()})"
