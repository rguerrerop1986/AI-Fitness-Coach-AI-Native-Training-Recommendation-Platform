from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.http import FileResponse, Http404
from apps.common.permissions import IsCoachOrAssistant, IsClient, get_client_from_user
from .models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle, TrainingEntry, Meal
from .serializers import (
    DietPlanSerializer, WorkoutPlanSerializer, PlanAssignmentSerializer,
    PlanCycleSerializer, PlanCycleDetailSerializer, ClientPlanCycleSerializer,
    TrainingEntrySerializer, MealSerializer
)
from .services.pdf_service import generate_plan_pdf


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
    
    def create(self, request, *args, **kwargs):
        """Create PlanCycle with optional period_days helper."""
        data = request.data.copy()
        
        # Handle period_days helper
        if 'period_days' in data and 'start_date' not in data:
            period_days = data.pop('period_days')
            # Handle both string and number inputs
            if isinstance(period_days, list):
                period_days = int(period_days[0])
            else:
                period_days = int(period_days)
            
            today = timezone.now().date()
            data['start_date'] = today.isoformat()
            data['end_date'] = (today + timedelta(days=period_days - 1)).isoformat()
        
        # Always set coach to current user (don't allow override)
        data['coach'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        client = serializer.validated_data.get('client')
        if client and not client.is_active:
            return Response(
                {'detail': 'El cliente está inactivo. No se pueden crear planes.'},
                status=status.HTTP_409_CONFLICT,
            )
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='set-status')
    def set_status(self, request, pk=None):
        """
        Update plan cycle status (coach only).
        Allowed transitions: DRAFT -> SAVED, DRAFT -> PUBLISHED, SAVED -> PUBLISHED.
        Publishing requires diet plan and workout plan to exist and be non-empty.
        """
        cycle = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'status is required (saved or published)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        new_status = str(new_status).lower().strip()
        if new_status not in (PlanCycle.Status.SAVED, PlanCycle.Status.PUBLISHED):
            return Response(
                {'error': 'status must be "saved" or "published"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        current = cycle.status
        if current not in (PlanCycle.Status.DRAFT, PlanCycle.Status.SAVED, PlanCycle.Status.PUBLISHED):
            return Response(
                {'error': f'Cannot change status from {current}. Only draft/saved plans can be updated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_status == PlanCycle.Status.PUBLISHED:
            # Require diet plan and workout plan to exist and be non-empty
            has_diet = hasattr(cycle, 'diet_plan') and cycle.diet_plan is not None
            has_workout = hasattr(cycle, 'workout_plan') and cycle.workout_plan is not None
            if not has_diet or not has_workout:
                return Response(
                    {
                        'error': 'Cannot publish: plan must have both a diet plan and a workout plan.',
                        'has_diet_plan': has_diet,
                        'has_workout_plan': has_workout,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            diet_empty = not cycle.diet_plan.meals.exists()
            workout_has_entries = TrainingEntry.objects.filter(workout_plan=cycle.workout_plan).exists()
            workout_has_days = cycle.workout_plan.workout_days.exists() if has_workout else False
            if diet_empty:
                return Response(
                    {'error': 'Cannot publish: diet plan must have at least one meal.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not workout_has_entries and not workout_has_days:
                return Response(
                    {'error': 'Cannot publish: workout plan must have at least one workout day or training entry.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        cycle.status = new_status
        cycle.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(cycle)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post', 'patch'], url_path='diet-plan')
    def diet_plan(self, request, pk=None):
        """Nested endpoint for diet plan of a cycle."""
        cycle = self.get_object()
        
        if request.method == 'GET':
            if hasattr(cycle, 'diet_plan') and cycle.diet_plan:
                serializer = DietPlanSerializer(cycle.diet_plan)
                return Response(serializer.data)
            return Response({'detail': 'No diet plan found for this cycle.'}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method == 'POST':
            # Create diet plan
            if hasattr(cycle, 'diet_plan') and cycle.diet_plan:
                return Response(
                    {'detail': 'Diet plan already exists for this cycle. Use PATCH to update.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate client-provided fields only; set relations on save
            serializer = DietPlanSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(plan_cycle=cycle, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'PATCH':
            if not hasattr(cycle, 'diet_plan') or not cycle.diet_plan:
                return Response(
                    {'detail': 'Diet plan does not exist. Use POST to create.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = DietPlanSerializer(cycle.diet_plan, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='diet-plan/meals')
    def diet_plan_meals(self, request, pk=None):
        """Add a meal to the diet plan of a cycle."""
        cycle = self.get_object()
        
        if not hasattr(cycle, 'diet_plan') or not cycle.diet_plan:
            return Response(
                {'detail': 'Diet plan does not exist. Create it first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # DRF's request.data is already a dict for JSON requests
        # Just ensure we have a clean dict
        data = dict(request.data)
        data['diet_plan'] = cycle.diet_plan.id
        
        # Normalize order to integer
        if 'order' in data and data['order'] is not None:
            try:
                data['order'] = int(data['order'])
            except (ValueError, TypeError):
                pass
        
        # Check for existing meals BEFORE serializer validation
        from .models import Meal
        meal_type_val = data.get('meal_type')
        order_val = data.get('order')
        
        if meal_type_val is not None and order_val is not None:
            # Use select_for_update to prevent race conditions, or just a simple check
            existing_meal = Meal.objects.filter(
                diet_plan=cycle.diet_plan,
                meal_type=meal_type_val,
                order=order_val
            ).first()
            
            if existing_meal:
                # Return error before serializer validation with detailed info
                all_meals = Meal.objects.filter(diet_plan=cycle.diet_plan).values('id', 'meal_type', 'order', 'name')
                return Response(
                    {
                        'detail': (
                            f'A meal with type "{meal_type_val}" and order "{order_val}" already exists for this diet plan. '
                            'Adjust the "order" or meal type, or update the existing meal instead.'
                        ),
                        'existing_meal_id': existing_meal.id,
                        'existing_meal_name': existing_meal.name or 'Unnamed',
                        'all_meals': list(all_meals) if settings.DEBUG else None
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        serializer = MealSerializer(data=data)
        if not serializer.is_valid():
            # Return detailed validation errors
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            meal = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            # Most likely unique_together(diet_plan, meal_type, order) violation
            # Check what actually exists to provide better error message
            from .models import Meal
            meal_type_val = data.get('meal_type')
            order_val = data.get('order')
            
            # Try to find existing meal
            existing_meal = None
            if meal_type_val is not None and order_val is not None:
                existing_meal = Meal.objects.filter(
                    diet_plan=cycle.diet_plan,
                    meal_type=meal_type_val,
                    order=order_val
                ).first()
            
            # Also check all meals for this diet plan for debugging
            all_meals = Meal.objects.filter(diet_plan=cycle.diet_plan).values('id', 'meal_type', 'order')
            
            error_msg = (
                'A meal with this type and order already exists for this diet plan. '
                'Adjust the "order" or meal type.'
            )
            if existing_meal:
                error_msg += f' (Existing meal ID: {existing_meal.id})'
            
            response_data = {
                'detail': error_msg,
                'error': str(e)
            }
            
            if settings.DEBUG:
                response_data['debug'] = {
                    'attempted': {'meal_type': meal_type_val, 'order': order_val, 'diet_plan_id': cycle.diet_plan.id},
                    'all_meals': list(all_meals),
                    'existing_meal_id': existing_meal.id if existing_meal else None,
                    'raw_request_data': dict(request.data) if hasattr(request.data, 'items') else str(request.data)
                }
            
            return Response(
                response_data,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch any other unexpected errors
            import traceback
            return Response(
                {
                    'detail': f'Failed to create meal: {str(e)}',
                    'error': str(e),
                    'traceback': traceback.format_exc() if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=['get', 'post', 'patch'], url_path='workout-plan')
    def workout_plan(self, request, pk=None):
        """Nested endpoint for workout plan of a cycle."""
        cycle = self.get_object()
        
        if request.method == 'GET':
            if hasattr(cycle, 'workout_plan') and cycle.workout_plan:
                serializer = WorkoutPlanSerializer(cycle.workout_plan)
                return Response(serializer.data)
            return Response({'detail': 'No workout plan found for this cycle.'}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method == 'POST':
            # Create workout plan
            if hasattr(cycle, 'workout_plan') and cycle.workout_plan:
                return Response(
                    {'detail': 'Workout plan already exists for this cycle. Use PATCH to update.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate client-provided fields only; set relations on save
            serializer = WorkoutPlanSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(plan_cycle=cycle, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif request.method == 'PATCH':
            if not hasattr(cycle, 'workout_plan') or not cycle.workout_plan:
                return Response(
                    {'detail': 'Workout plan does not exist. Use POST to create.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = WorkoutPlanSerializer(cycle.workout_plan, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='generate-pdf')
    def generate_pdf(self, request, pk=None):
        """Generate PDF for the plan cycle."""
        cycle = self.get_object()
        
        try:
            pdf_buffer = generate_plan_pdf(cycle)
            
            # Save to PlanCycle
            from django.core.files.base import ContentFile
            filename = f"plan_{cycle.client.full_name.replace(' ', '_')}_{cycle.start_date}_{cycle.end_date}.pdf"
            cycle.plan_pdf.save(filename, ContentFile(pdf_buffer.read()), save=True)
            
            return Response(
                {
                    'message': 'PDF generated successfully',
                    'download_url': f'/api/plans/plan-cycles/{cycle.id}/download-pdf/'
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            # Explicit error when PDF is considered "empty" or too small
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(detail=True, methods=['get'], url_path='download-pdf')
    def download_pdf(self, request, pk=None):
        """Download the generated PDF."""
        cycle = self.get_object()
        
        if not cycle.plan_pdf:
            return Response(
                {'error': 'PDF not generated yet. Generate it first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            response = FileResponse(cycle.plan_pdf.open('rb'), content_type='application/pdf')
            filename = cycle.plan_pdf.name.split('/')[-1]
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Cache-Control'] = 'no-store'
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to download PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current published cycle for a client (coach view)."""
        client_id = request.query_params.get('client')
        if not client_id:
            return Response(
                {'error': 'client parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cycle = PlanCycle.objects.filter(
                client_id=client_id,
                status=PlanCycle.Status.PUBLISHED
            ).order_by('-start_date').first()
            
            if not cycle:
                return Response(
                    {'error': 'No published cycle found for this client'},
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
    API view for clients to view their current published PlanCycle.
    """
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        """Return current published cycle or 404."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        cycle = PlanCycle.objects.filter(
            client=client,
            status=PlanCycle.Status.PUBLISHED
        ).order_by('-start_date').first()
        
        if not cycle:
            return Response(
                {'error': 'No published plan found. Your coach has not published your plan yet.'},
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


class MealViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meals in diet plans (coach only)."""
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    
    def get_queryset(self):
        """Filter by diet_plan if provided."""
        queryset = super().get_queryset()
        diet_plan_id = self.request.query_params.get('diet_plan')
        if diet_plan_id:
            queryset = queryset.filter(diet_plan_id=diet_plan_id)
        return queryset
