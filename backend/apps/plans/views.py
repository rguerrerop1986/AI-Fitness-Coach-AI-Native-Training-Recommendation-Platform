from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.common.permissions import IsCoachOrAssistant, IsClient, get_client_from_user
from .models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle, TrainingEntry
from .serializers import (
    DietPlanSerializer, WorkoutPlanSerializer, PlanAssignmentSerializer,
    PlanCycleSerializer, PlanCycleDetailSerializer, ClientPlanCycleSerializer,
    TrainingEntrySerializer
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
    
    @action(detail=True, methods=['get', 'post'])
    def entries(self, request, pk=None):
        """Nested endpoint for training entries of a workout plan."""
        workout_plan = self.get_object()
        
        if request.method == 'GET':
            entries = TrainingEntry.objects.filter(workout_plan=workout_plan).order_by('date', 'id')
            serializer = TrainingEntrySerializer(entries, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = TrainingEntrySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(workout_plan=workout_plan)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class TrainingEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing training entries in workout plans.
    
    - Coach: Full CRUD on entries for any workout plan
    - Client: Read-only access to entries in their assigned plans
    """
    queryset = TrainingEntry.objects.all()
    serializer_class = TrainingEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['workout_plan', 'exercise', 'date']
    ordering_fields = ['date', 'created_at']
    ordering = ['date', 'id']
    
    def get_permissions(self):
        """Different permissions for read vs write operations."""
        if self.action in ['list', 'retrieve']:
            # Read access for all authenticated users
            return [IsAuthenticated()]
        else:
            # Write access only for coach/assistant
            return [IsAuthenticated(), IsCoachOrAssistant()]
    
    def get_queryset(self):
        """Filter entries based on user role."""
        queryset = super().get_queryset()
        
        # If client, only show entries from their assigned plans
        if self.request.user.role == 'client':
            client = get_client_from_user(self.request.user)
            if not client:
                return TrainingEntry.objects.none()
            
            # Get workout plans assigned to this client
            from .models import PlanAssignment
            assigned_plans = PlanAssignment.objects.filter(
                client=client,
                plan_type='workout',
                is_active=True,
                workout_plan__isnull=False
            ).values_list('workout_plan_id', flat=True)
            
            queryset = queryset.filter(workout_plan_id__in=assigned_plans)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set workout_plan if provided in URL."""
        workout_plan_id = self.request.data.get('workout_plan')
        if workout_plan_id:
            serializer.save(workout_plan_id=workout_plan_id)
        else:
            serializer.save()
