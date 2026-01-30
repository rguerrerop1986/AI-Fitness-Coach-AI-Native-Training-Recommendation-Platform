from rest_framework import serializers
from .models import ClientAccessLog
from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle


class ClientDashboardSerializer(serializers.ModelSerializer):
    """Serializer for client dashboard data."""
    latest_measurement = serializers.SerializerMethodField()
    active_diet_plan = serializers.SerializerMethodField()
    active_workout_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'email', 'height_cm',
            'initial_weight_kg', 'latest_measurement', 'active_diet_plan',
            'active_workout_plan'
        ]
    
    def get_latest_measurement(self, obj):
        latest = obj.measurements.first()
        if latest:
            return {
                'date': latest.date,
                'weight_kg': latest.weight_kg,
                'body_fat_pct': latest.body_fat_pct,
                'chest_cm': latest.chest_cm,
                'waist_cm': latest.waist_cm,
                'hips_cm': latest.hips_cm,
                'bicep_cm': latest.bicep_cm,
                'thigh_cm': latest.thigh_cm,
                'calf_cm': latest.calf_cm,
            }
        return None
    
    def get_active_diet_plan(self, obj):
        # Prefer published PlanCycle (same source as "Mi plan")
        cycle = PlanCycle.objects.filter(
            client=obj,
            status=PlanCycle.Status.PUBLISHED
        ).order_by('-start_date').first()
        if cycle and hasattr(cycle, 'diet_plan') and cycle.diet_plan:
            dp = cycle.diet_plan
            return {
                'id': dp.id,
                'title': dp.title or '',
                'goal': dp.goal or '',
                'daily_calories': dp.daily_calories,
                'version': dp.version,
                'assigned_date': cycle.start_date,
            }
        # Fallback: legacy PlanAssignment
        active_assignment = obj.planassignment_set.filter(
            plan_type='diet',
            is_active=True
        ).first()
        if active_assignment and active_assignment.diet_plan:
            return {
                'id': active_assignment.diet_plan.id,
                'title': active_assignment.diet_plan.title,
                'goal': active_assignment.diet_plan.goal,
                'daily_calories': active_assignment.diet_plan.daily_calories,
                'version': active_assignment.diet_plan.version,
                'assigned_date': active_assignment.start_date,
            }
        return None

    def get_active_workout_plan(self, obj):
        # Prefer published PlanCycle (same source as "Mi plan")
        cycle = PlanCycle.objects.filter(
            client=obj,
            status=PlanCycle.Status.PUBLISHED
        ).order_by('-start_date').first()
        if cycle and hasattr(cycle, 'workout_plan') and cycle.workout_plan:
            wp = cycle.workout_plan
            return {
                'id': wp.id,
                'title': wp.title or '',
                'goal': wp.goal or '',
                'version': wp.version,
                'assigned_date': cycle.start_date,
            }
        # Fallback: legacy PlanAssignment
        active_assignment = obj.planassignment_set.filter(
            plan_type='workout',
            is_active=True
        ).first()
        if active_assignment and active_assignment.workout_plan:
            return {
                'id': active_assignment.workout_plan.id,
                'title': active_assignment.workout_plan.title,
                'goal': active_assignment.workout_plan.goal,
                'version': active_assignment.workout_plan.version,
                'assigned_date': active_assignment.start_date,
            }
        return None


class DietPlanDetailSerializer(serializers.ModelSerializer):
    """Detailed diet plan serializer for client view."""
    meals = serializers.SerializerMethodField()
    total_nutrition = serializers.SerializerMethodField()
    
    class Meta:
        model = DietPlan
        fields = [
            'id', 'title', 'description', 'goal', 'daily_calories',
            'protein_pct', 'carbs_pct', 'fat_pct', 'version',
            'created_at', 'meals', 'total_nutrition'
        ]
    
    def get_meals(self, obj):
        meals_data = []
        for meal in obj.meals.all():
            meal_items = []
            for item in meal.items.all():
                meal_items.append({
                    'food_name': item.food.name,
                    'quantity': item.quantity,
                    'unit': item.food.unit,
                    'calories': item.total_calories,
                    'protein': item.total_protein,
                    'carbs': item.total_carbs,
                    'fat': item.total_fat,
                })
            
            meals_data.append({
                'meal_type': meal.meal_type,
                'name': meal.name,
                'items': meal_items,
            })
        return meals_data
    
    def get_total_nutrition(self, obj):
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for meal in obj.meals.all():
            for item in meal.items.all():
                total_calories += item.total_calories
                total_protein += item.total_protein
                total_carbs += item.total_carbs
                total_fat += item.total_fat
        
        return {
            'calories': round(total_calories, 1),
            'protein_g': round(total_protein, 1),
            'carbs_g': round(total_carbs, 1),
            'fat_g': round(total_fat, 1),
        }


class WorkoutPlanDetailSerializer(serializers.ModelSerializer):
    """Detailed workout plan serializer for client view."""
    workout_days = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'title', 'description', 'goal', 'version',
            'created_at', 'workout_days'
        ]
    
    def get_workout_days(self, obj):
        days_data = []
        for day in obj.workout_days.all():
            exercises = []
            for exercise_set in day.exercise_sets.all():
                exercises.append({
                    'exercise_name': exercise_set.exercise.name,
                    'sets': exercise_set.sets,
                    'reps_or_time': exercise_set.reps_or_time,
                    'set_type': exercise_set.set_type,
                    'rest_seconds': exercise_set.rest_seconds,
                    'exercise_description': exercise_set.exercise.description,
                })
            
            days_data.append({
                'day_of_week': day.day_of_week,
                'name': day.name,
                'exercises': exercises,
            })
        return days_data
