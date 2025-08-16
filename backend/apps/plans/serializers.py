from rest_framework import serializers
from .models import DietPlan, WorkoutPlan, PlanAssignment, Meal, MealItem, WorkoutDay, ExerciseSet


class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = ['id', 'food', 'quantity']


class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Meal
        fields = ['id', 'name', 'meal_type', 'items']


class DietPlanSerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)
    
    class Meta:
        model = DietPlan
        fields = [
            'id', 'title', 'description', 'goal', 'daily_calories',
            'protein_pct', 'carbs_pct', 'fat_pct', 'is_active',
            'version', 'created_at', 'updated_at', 'meals'
        ]


class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['id', 'exercise', 'sets', 'reps', 'duration_minutes', 'rest_seconds']


class WorkoutDaySerializer(serializers.ModelSerializer):
    exercise_sets = ExerciseSetSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutDay
        fields = ['id', 'day_of_week', 'name', 'exercise_sets']


class WorkoutPlanSerializer(serializers.ModelSerializer):
    workout_days = WorkoutDaySerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'title', 'description', 'goal', 'is_active',
            'version', 'created_at', 'updated_at', 'workout_days'
        ]


class PlanAssignmentSerializer(serializers.ModelSerializer):
    diet_plan = DietPlanSerializer(read_only=True)
    workout_plan = WorkoutPlanSerializer(read_only=True)
    
    class Meta:
        model = PlanAssignment
        fields = [
            'id', 'client', 'diet_plan', 'workout_plan',
            'start_date', 'end_date', 'is_active', 'created_at'
        ]
