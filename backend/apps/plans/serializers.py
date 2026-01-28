from rest_framework import serializers
from .models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle, Meal, MealItem, WorkoutDay, ExerciseSet, TrainingEntry
from apps.clients.serializers import ClientSerializer
from apps.catalogs.serializers import ExerciseSerializer


class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = ['id', 'food', 'quantity']


class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)
    
    class Meta:
        model = Meal
        fields = ['id', 'diet_plan', 'name', 'meal_type', 'meal_type_display', 'description', 'items', 'order']
        read_only_fields = ['id']


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


class TrainingEntrySerializer(serializers.ModelSerializer):
    """Serializer for training entries in workout plans."""
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    
    class Meta:
        model = TrainingEntry
        fields = [
            'id', 'workout_plan', 'exercise', 'exercise_detail',
            'date', 'series', 'repetitions', 'weight_kg',
            'rest_seconds', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate business rules."""
        if not attrs.get('repetitions') or not attrs.get('repetitions').strip():
            raise serializers.ValidationError({
                'repetitions': 'Repetitions field is required.'
            })
        
        weight_kg = attrs.get('weight_kg')
        if weight_kg is not None and weight_kg < 0:
            raise serializers.ValidationError({
                'weight_kg': 'Weight must be non-negative.'
            })
        
        rest_seconds = attrs.get('rest_seconds')
        if rest_seconds is not None and rest_seconds < 0:
            raise serializers.ValidationError({
                'rest_seconds': 'Rest seconds must be non-negative.'
            })
        
        return attrs


class WorkoutPlanSerializer(serializers.ModelSerializer):
    workout_days = WorkoutDaySerializer(many=True, read_only=True)
    training_entries = TrainingEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutPlan
        fields = [
            'id', 'title', 'description', 'goal', 'is_active',
            'version', 'created_at', 'updated_at', 'workout_days', 'training_entries'
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
    diet_plan_data = serializers.SerializerMethodField()
    workout_plan_data = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PlanCycle
        fields = [
            'id', 'start_date', 'end_date', 'cadence', 'goal', 'status',
            'is_active', 'duration_days', 'diet_plan_data', 'workout_plan_data'
        ]
        read_only_fields = fields
    
    def get_diet_plan_data(self, obj):
        """Get diet plan linked to this cycle."""
        if hasattr(obj, 'diet_plan') and obj.diet_plan:
            meals = obj.diet_plan.meals.all().order_by('order', 'meal_type')
            return {
                'id': obj.diet_plan.id,
                'title': obj.diet_plan.title,
                'goal': obj.diet_plan.goal,
                'daily_calories': obj.diet_plan.daily_calories,
                'meals': MealSerializer(meals, many=True).data,
            }
        return None
    
    def get_workout_plan_data(self, obj):
        """Get workout plan linked to this cycle with training entries."""
        if hasattr(obj, 'workout_plan') and obj.workout_plan:
            entries = TrainingEntry.objects.filter(
                workout_plan=obj.workout_plan
            ).order_by('date', 'id')
            
            entries_data = TrainingEntrySerializer(entries, many=True).data
            
            return {
                'id': obj.workout_plan.id,
                'title': obj.workout_plan.title,
                'goal': obj.workout_plan.goal,
                'training_entries': entries_data,
            }
        return None
