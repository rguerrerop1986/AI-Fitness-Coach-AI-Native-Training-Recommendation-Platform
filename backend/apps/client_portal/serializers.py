from rest_framework import serializers
from .models import ClientAccessLog
from apps.clients.models import Client, Measurement
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle
from apps.tracking.models import DailyExerciseRecommendation
from apps.catalogs.models import Exercise


class ClientDashboardSerializer(serializers.ModelSerializer):
    """Serializer for client dashboard data."""
    latest_measurement = serializers.SerializerMethodField()
    active_diet_plan = serializers.SerializerMethodField()
    active_workout_plan = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'email', 'height_m',
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


class DailyExerciseRecommendationSerializer(serializers.ModelSerializer):
    """Daily exercise recommendation for client plan view."""
    exercise_name = serializers.SerializerMethodField()
    exercise_instructions = serializers.SerializerMethodField()
    exercise_video_url = serializers.SerializerMethodField()
    exercise_image_url = serializers.SerializerMethodField()
    exercise_equipment = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    warning = serializers.SerializerMethodField()

    class Meta:
        model = DailyExerciseRecommendation
        fields = [
            'id', 'date', 'intensity', 'type', 'rationale', 'status',
            'exercise', 'exercise_name', 'exercise_instructions', 'exercise_video_url', 'exercise_image_url',
            'exercise_equipment', 'duration_minutes', 'warning', 'metadata',
        ]

    def _exercise_field(self, obj, attr, default=''):
        return getattr(obj.exercise, attr, None) or default if obj.exercise else default

    def get_exercise_name(self, obj):
        return self._exercise_field(obj, 'name', 'Ejercicio recomendado')

    def get_exercise_instructions(self, obj):
        return self._exercise_field(obj, 'instructions', '')

    def get_exercise_video_url(self, obj):
        return self._exercise_field(obj, 'video_url', '')

    def get_exercise_image_url(self, obj):
        return self._exercise_field(obj, 'image_url', '')

    def get_exercise_equipment(self, obj):
        if obj.exercise and obj.exercise.equipment_type:
            return obj.exercise.get_equipment_type_display()
        return ''

    def get_duration_minutes(self, obj):
        return obj.metadata.get('duration_minutes') or 20

    def get_warning(self, obj):
        rules = obj.metadata.get('applied_rules') or []
        if 'pain_high_mobility' in rules:
            return 'Dolor elevado recientemente: priorizamos descanso activo. Si persiste, consulta a tu médico.'
        if 'pain_moderate_no_hiit' in rules:
            return 'Evita impacto hoy; priorizamos movilidad y core suave.'
        return None


class CompleteDailyExerciseSerializer(serializers.Serializer):
    """Request body for POST complete: post-workout metrics (closed-loop V1.1)."""
    rpe = serializers.IntegerField(min_value=1, max_value=10)
    energy_level = serializers.IntegerField(min_value=1, max_value=10)
    pain_level = serializers.IntegerField(min_value=0, max_value=10)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    executed_exercise_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_executed_exercise_id(self, value):
        if value is None:
            return value
        if not Exercise.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Ejercicio no encontrado o inactivo.')
        return value
