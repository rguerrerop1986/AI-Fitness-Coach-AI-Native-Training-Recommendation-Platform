from rest_framework import serializers
from .models import Food, Exercise


class FoodSerializer(serializers.ModelSerializer):
    """Serializer for food catalog."""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Food
        fields = [
            'id', 'name', 'brand', 'full_name', 'serving_size', 'kcal', 
            'protein_g', 'carbs_g', 'fat_g', 'tags', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for exercise catalog."""
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'name', 'muscle_group', 'equipment', 'difficulty', 
            'instructions', 'video_url', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
