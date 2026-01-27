from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.common.permissions import IsCoachOrAssistant, IsClient, get_client_from_user
from .models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle
from .serializers import (
    DietPlanSerializer, WorkoutPlanSerializer, PlanAssignmentSerializer,
    PlanCycleSerializer, PlanCycleDetailSerializer, ClientPlanCycleSerializer
)


class DietPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diet plans (coach only).
    """
    queryset = DietPlan.objects.all()
    serializer_class = DietPlanSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filterset_fields = ['goal', 'is_active']
    search_fields = ['title', 'description']


class WorkoutPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workout plans (coach only).
    """
    queryset = WorkoutPlan.objects.all()
    serializer_class = WorkoutPlanSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filterset_fields = ['goal', 'is_active']
    search_fields = ['title', 'description']


class PlanAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing plan assignments to clients (coach only).
    """
    queryset = PlanAssignment.objects.all()
    serializer_class = PlanAssignmentSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]


class PlanCycleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing PlanCycles (coach only).
    """
    queryset = PlanCycle.objects.all()
    serializer_class = PlanCycleSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filterset_fields = ['client', 'status', 'cadence', 'goal']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlanCycleDetailSerializer
        return PlanCycleSerializer
    
    def get_queryset(self):
        """Filter by client if provided."""
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active cycle for a client (coach view)."""
        client_id = request.query_params.get('client')
        if not client_id:
            return Response(
                {'error': 'client parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cycle = PlanCycle.objects.filter(
                client_id=client_id,
                status=PlanCycle.Status.ACTIVE
            ).first()
            
            if not cycle:
                return Response(
                    {'error': 'No active cycle found for this client'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = PlanCycleDetailSerializer(cycle)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ClientCurrentCycleView(APIView):
    """
    API view for clients to view their current active PlanCycle.
    """
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        """Return current active cycle or 404."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cycle = PlanCycle.objects.filter(
            client=client,
            status=PlanCycle.Status.ACTIVE
        ).first()
        
        if not cycle:
            return Response(
                {'error': 'No active cycle found. Contact your coach.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClientPlanCycleSerializer(cycle)
        return Response(serializer.data)
    filterset_fields = ['client', 'diet_plan', 'workout_plan', 'is_active']
