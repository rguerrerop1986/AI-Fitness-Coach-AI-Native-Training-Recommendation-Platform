from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import DietPlan, WorkoutPlan, PlanAssignment
from .serializers import DietPlanSerializer, WorkoutPlanSerializer, PlanAssignmentSerializer


class DietPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diet plans.
    """
    queryset = DietPlan.objects.all()
    serializer_class = DietPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['goal', 'is_active']
    search_fields = ['title', 'description']


class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workout plans.
    """
    queryset = WorkoutPlan.objects.all()
    serializer_class = WorkoutPlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['goal', 'is_active']
    search_fields = ['title', 'description']


class PlanAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing plan assignments to clients.
    """
    queryset = PlanAssignment.objects.all()
    serializer_class = PlanAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['client', 'diet_plan', 'workout_plan', 'is_active']
