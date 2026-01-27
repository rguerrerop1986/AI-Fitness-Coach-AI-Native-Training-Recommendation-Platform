from rest_framework import serializers
from .models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle, Meal, MealItem, WorkoutDay, ExerciseSet
from apps.clients.serializers import ClientSerializer


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
            'start_date', 'end_date', 'is_active', 'plan_cycle', 'created_at'
        ]


class PlanCycleSerializer(serializers.ModelSerializer):
    """Serializer for PlanCycle (coach view)."""
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    assignment_count = serializers.SerializerMethodField()
    checkin_count = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PlanCycle
        fields = [
            'id', 'client', 'client_name', 'coach', 'coach_name',
            'start_date', 'end_date', 'cadence', 'goal', 'status',
            'notes', 'is_active', 'duration_days', 'assignment_count',
            'checkin_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    
    def get_checkin_count(self, obj):
        return obj.checkins.count()


class PlanCycleDetailSerializer(PlanCycleSerializer):
    """Detailed serializer for PlanCycle with assignments and check-ins."""
    assignments = PlanAssignmentSerializer(many=True, read_only=True, source='assignments.all')
    
    class Meta(PlanCycleSerializer.Meta):
        fields = PlanCycleSerializer.Meta.fields + ['assignments']


class ClientPlanCycleSerializer(serializers.ModelSerializer):
    """Simplified serializer for client view of their current cycle."""
    diet_plan_summary = serializers.SerializerMethodField()
    workout_plan_summary = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PlanCycle
        fields = [
            'id', 'start_date', 'end_date', 'cadence', 'goal', 'status',
            'is_active', 'duration_days', 'diet_plan_summary', 'workout_plan_summary'
        ]
        read_only_fields = fields
    
    def get_diet_plan_summary(self, obj):
        """Get active diet plan assigned to this cycle."""
        diet_assignment = obj.assignments.filter(
            plan_type='diet',
            is_active=True,
            diet_plan__isnull=False
        ).first()
        
        if diet_assignment and diet_assignment.diet_plan:
            return {
                'id': diet_assignment.diet_plan.id,
                'title': diet_assignment.diet_plan.title,
                'goal': diet_assignment.diet_plan.goal,
                'daily_calories': diet_assignment.diet_plan.daily_calories,
            }
        return None
    
    def get_workout_plan_summary(self, obj):
        """Get active workout plan assigned to this cycle."""
        workout_assignment = obj.assignments.filter(
            plan_type='workout',
            is_active=True,
            workout_plan__isnull=False
        ).first()
        
        if workout_assignment and workout_assignment.workout_plan:
            return {
                'id': workout_assignment.workout_plan.id,
                'title': workout_assignment.workout_plan.title,
                'goal': workout_assignment.workout_plan.goal,
            }
        return None
