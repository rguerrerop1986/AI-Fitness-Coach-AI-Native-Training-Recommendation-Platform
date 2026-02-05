from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Food(models.Model):
    """Food catalog model with nutritional information."""
    
    class NutritionalGroup(models.TextChoices):
        CEREALES_TUBERCULOS_DERIVADOS = 'cereales_tuberculos_derivados', 'Cereales, tubérculos y derivados.'
        FRUTAS_VERDURAS = 'frutas_verduras', 'Frutas y verduras.'
        LECHE_DERIVADOS = 'leche_derivados', 'Leche y derivados.'
        CARNES_LEGUMBRES_HUEVOS = 'carnes_legumbres_huevos', 'Carnes, legumbres secas y huevos.'
        AZUCARES_MIELES = 'azucares_mieles', 'Azúcares o mieles.'
        ACEITES_GRASAS = 'aceites_grasas', 'Aceites o grasas.'
    
    class OriginClassification(models.TextChoices):
        VEGETAL = 'vegetal', 'Vegetal'
        ANIMAL = 'animal', 'Animal'
        MINERAL = 'mineral', 'Mineral'
    
    name = models.CharField(max_length=200, unique=True, help_text="Food name (unique)")
    brand = models.CharField(max_length=100, blank=True)
    
    # Classification fields
    nutritional_group = models.CharField(
        max_length=30,
        choices=NutritionalGroup.choices,
        null=True,
        blank=True,
        help_text="Nutritional group classification"
    )
    origin_classification = models.CharField(
        max_length=10,
        choices=OriginClassification.choices,
        null=True,
        blank=True,
        help_text="Origin classification"
    )
    
    # Serving information (kept for backward compatibility)
    serving_size = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        validators=[MinValueValidator(0.1)],
        help_text="Serving size in grams or milliliters",
        default=100.0
    )
    
    # Macronutrients (per 100g)
    calories_kcal = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Calories per 100g (kcal)"
    )
    protein_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Protein in grams per 100g"
    )
    carbs_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Carbohydrates in grams per 100g"
    )
    fats_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fats in grams per 100g"
    )
    
    # Optional nutrition fields
    fiber_g = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fiber in grams per 100g (optional)"
    )
    water_g = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Water in grams per 100g (optional)"
    )
    creatine_mg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Creatine in milligrams per 100g (optional)"
    )
    
    # Text fields
    micronutrients_notes = models.TextField(blank=True, help_text="Notes about micronutrients")
    notes = models.TextField(blank=True, help_text="General notes, sources, remarks")
    
    # Legacy fields (kept for backward compatibility - per serving)
    kcal = models.DecimalField(
        max_digits=6, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Calories per serving (legacy - use calories_kcal per 100g)"
    )
    fat_g = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fat in grams per serving (legacy - use fats_g per 100g)"
    )
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for categorization")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'foods'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['nutritional_group']),
            models.Index(fields=['origin_classification']),
        ]
    
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
    
    class EquipmentType(models.TextChoices):
        MANCUERNA = 'mancuerna', 'Mancuerna'
        BARRA = 'barra', 'Barra'
        MAQUINA = 'maquina', 'Máquina'
        PESO_CORPORAL = 'peso_corporal', 'Peso Corporal'
        BANDA = 'banda', 'Banda de Resistencia'
        CABLE = 'cable', 'Cable'
        KETTLEBELL = 'kettlebell', 'Kettlebell'
        OTRO = 'otro', 'Otro'
    
    name = models.CharField(max_length=200, unique=True, help_text="Exercise name (unique)")
    muscle_group = models.CharField(max_length=20, choices=MuscleGroup.choices, help_text="Muscle group")
    equipment_type = models.CharField(
        max_length=20,
        choices=EquipmentType.choices,
        null=True,
        blank=True,
        help_text="Type of equipment required"
    )
    equipment = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific equipment name (legacy field, use equipment_type)"
    )
    difficulty = models.CharField(
        max_length=15,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER
    )
    # Recommendation/ML: intensity 1-10, tags for filtering (e.g. hiit, mobility, low_impact)
    intensity = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Intensity level 1-10 for recommendation engine',
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Tags for filtering: e.g. ["hiit", "mobility", "low_impact"]',
    )
    instructions = models.TextField(help_text="Exercise instructions (text or URL)")
    image_url = models.URLField(
        blank=True,
        help_text="Optional image URL for the exercise"
    )
    video_url = models.URLField(
        blank=True,
        help_text="Optional video demonstration URL"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exercises'
        ordering = ['muscle_group', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['muscle_group']),
            models.Index(fields=['equipment_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_muscle_group_display()})"
