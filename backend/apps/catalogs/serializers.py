from rest_framework import serializers
from .models import Food, Exercise


class FoodSerializer(serializers.ModelSerializer):
    """Serializer for food catalog with complete nutrition data."""
    full_name = serializers.ReadOnlyField()
    nutritional_group_display = serializers.SerializerMethodField()
    origin_classification_display = serializers.SerializerMethodField()
    
    def get_nutritional_group_display(self, obj):
        """Safely get nutritional group display, handling null values."""
        if obj.nutritional_group:
            return obj.get_nutritional_group_display()
        return None
    
    def get_origin_classification_display(self, obj):
        """Safely get origin classification display, handling null values."""
        if obj.origin_classification:
            return obj.get_origin_classification_display()
        return None
    
    class Meta:
        model = Food
        fields = [
            'id', 'name', 'brand', 'full_name',
            'nutritional_group', 'nutritional_group_display',
            'origin_classification', 'origin_classification_display',
            'serving_size', 'calories_kcal', 'protein_g', 'carbs_g', 'fats_g',
            'fiber_g', 'water_g', 'creatine_mg',
            'micronutrients_notes', 'notes',
            'tags', 'is_active', 'created_at', 'updated_at',
            # Legacy fields (for backward compatibility)
            'kcal', 'fat_g'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 
                           'nutritional_group_display', 'origin_classification_display']
    
    def validate(self, attrs):
        """Validate that all numeric fields are non-negative and required fields are present."""
        # Required fields for new foods
        if not self.instance:  # Creating new food
            required_fields = ['name', 'nutritional_group', 'origin_classification', 
                             'calories_kcal', 'protein_g', 'carbs_g', 'fats_g']
            for field in required_fields:
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError({
                        field: f'{field} is required.'
                    })
        
        # Validate all numeric fields are non-negative
        numeric_fields = [
            'calories_kcal', 'protein_g', 'carbs_g', 'fats_g',
            'fiber_g', 'water_g', 'creatine_mg'
        ]
        
        for field in numeric_fields:
            value = attrs.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({
                    field: f'{field} must be non-negative.'
                })
        
        return attrs


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for exercise catalog."""
    muscle_group_display = serializers.SerializerMethodField()
    equipment_type_display = serializers.SerializerMethodField()
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    def get_muscle_group_display(self, obj):
        """Safely get muscle group display, handling null values."""
        if obj.muscle_group:
            return obj.get_muscle_group_display()
        return None
    
    def get_equipment_type_display(self, obj):
        """Safely get equipment type display, handling null values."""
        if obj.equipment_type:
            return obj.get_equipment_type_display()
        return None
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'muscle_group', 'muscle_group_display',
            'equipment_type', 'equipment_type_display',
            'equipment', 'difficulty', 'difficulty_display',
            'instructions', 'image_url', 'video_url',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at',
                           'muscle_group_display', 'equipment_type_display', 'difficulty_display']
    
    def validate(self, attrs):
        """Validate required fields for new exercises."""
        if not self.instance:  # Creating new exercise
            required_fields = ['name', 'muscle_group', 'equipment_type', 'instructions']
            for field in required_fields:
                if field not in attrs or attrs[field] is None:
                    raise serializers.ValidationError({
                        field: f'{field} is required.'
                    })
        return attrs


class FoodSearchSerializer(serializers.ModelSerializer):
    """Simplified serializer for food search results."""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Food
        fields = ['id', 'name', 'brand', 'full_name', 'serving_size', 'kcal', 'protein_g', 'carbs_g', 'fat_g']


class ExerciseSearchSerializer(serializers.ModelSerializer):
    """Simplified serializer for exercise search results."""
    
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'muscle_group', 'equipment', 'difficulty']
