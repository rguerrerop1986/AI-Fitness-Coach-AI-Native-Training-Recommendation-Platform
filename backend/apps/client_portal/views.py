import os
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from django.template import Context

from .models import ClientAccessLog
from .serializers import (
    ClientDashboardSerializer, DietPlanDetailSerializer, WorkoutPlanDetailSerializer,
    DailyExerciseRecommendationSerializer, CompleteDailyExerciseSerializer,
)
from apps.clients.models import Client
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle
from apps.plans.serializers import PlanAssignmentSerializer, ClientPlanCycleSerializer
from apps.common.permissions import IsClient, get_client_from_user
from apps.tracking.models import DailyExerciseRecommendation, TrainingLog
from apps.catalogs.models import Exercise
from apps.recommendations.services.daily_exercise import generate_daily_recommendation
from apps.recommendations.services.progression import (
    evaluate_outcome,
    apply_progression_update,
    get_or_create_progression_state,
)
from django.http import FileResponse


class ClientDashboardView(APIView):
    """Client dashboard endpoint."""
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        # Get client from user with guardrails
        client = get_client_from_user(request.user)
        if not client:
            return Response({
                'error': 'Client profile not found. Please contact your coach.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ClientDashboardSerializer(client)
        return Response(serializer.data)


class ClientCurrentPlanView(APIView):
    """API view for clients to view their current plan (diet + workout)."""
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        """Return current active cycle with full plan data."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only PUBLISHED plans are visible to clients
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


class ClientPlanPDFView(APIView):
    """API view for clients to download their plan PDF."""
    permission_classes = [IsAuthenticated, IsClient]
    
    def get(self, request):
        """Download PDF for client's current active cycle."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only PUBLISHED plans are visible to clients
        cycle = PlanCycle.objects.filter(
            client=client,
            status=PlanCycle.Status.PUBLISHED
        ).order_by('-start_date').first()
        
        if not cycle:
            return Response(
                {'error': 'No published plan found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not cycle.plan_pdf:
            return Response(
                {'error': 'PDF not generated yet. Contact your coach to generate it.'},
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


class ClientPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for client plan access (client only, own data only)."""
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = PlanAssignmentSerializer
    
    def get_queryset(self):
        # Get client from user with guardrails - NEVER use client_id param
        client = get_client_from_user(self.request.user)
        if not client:
            return PlanAssignment.objects.none()
        
        # Always filter by the client from request.user - ignore any client_id param
        return PlanAssignment.objects.filter(
            client=client,
            is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def diet_plan_detail(self, request, pk=None):
        """Get detailed diet plan information."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'diet' or not assignment.diet_plan:
            return Response({
                'error': 'No diet plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log access (client is inferred from request.user)
        client = get_client_from_user(request.user)
        if client:
            ClientAccessLog.objects.create(
                client=client,
                action='view_plan',
                plan_type='diet',
                plan_id=assignment.diet_plan.id,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = DietPlanDetailSerializer(assignment.diet_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def workout_plan_detail(self, request, pk=None):
        """Get detailed workout plan information."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'workout' or not assignment.workout_plan:
            return Response({
                'error': 'No workout plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log access (client is inferred from request.user)
        client = get_client_from_user(request.user)
        if client:
            ClientAccessLog.objects.create(
                client=client,
                action='view_plan',
                plan_type='workout',
                plan_id=assignment.workout_plan.id,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = WorkoutPlanDetailSerializer(assignment.workout_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download_diet_pdf(self, request, pk=None):
        """Download diet plan as PDF."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'diet' or not assignment.diet_plan:
            return Response({
                'error': 'No diet plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log download (client is inferred from request.user)
        client = get_client_from_user(request.user)
        if client:
            ClientAccessLog.objects.create(
                client=client,
                action='download_pdf',
                plan_type='diet',
                plan_id=assignment.diet_plan.id,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        # Generate PDF (use client from request.user)
        client = get_client_from_user(request.user)
        if not client:
            return Response({
                'error': 'Client profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        pdf_content = self.generate_diet_pdf(assignment.diet_plan, client)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="diet_plan_{assignment.diet_plan.title.replace(" ", "_")}.pdf"'
        return response
    
    @action(detail=True, methods=['get'])
    def download_workout_pdf(self, request, pk=None):
        """Download workout plan as PDF."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'workout' or not assignment.workout_plan:
            return Response({
                'error': 'No workout plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log download (client is inferred from request.user)
        client = get_client_from_user(request.user)
        if client:
            ClientAccessLog.objects.create(
                client=client,
                action='download_pdf',
                plan_type='workout',
                plan_id=assignment.workout_plan.id,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        # Generate PDF (use client from request.user)
        client = get_client_from_user(request.user)
        if not client:
            return Response({
                'error': 'Client profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        pdf_content = self.generate_workout_pdf(assignment.workout_plan, client)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="workout_plan_{assignment.workout_plan.title.replace(" ", "_")}.pdf"'
        return response
    
    def generate_diet_pdf(self, diet_plan, client):
        """Generate PDF for diet plan."""
        template = get_template('client_portal/diet_plan_pdf.html')
        
        # Get latest measurement
        latest_measurement = client.measurements.first()
        
        context = {
            'diet_plan': diet_plan,
            'client': client,
            'latest_measurement': latest_measurement,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
        }
        
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        else:
            return None
    
    def generate_workout_pdf(self, workout_plan, client):
        """Generate PDF for workout plan."""
        template = get_template('client_portal/workout_plan_pdf.html')
        
        # Get latest measurement
        latest_measurement = client.measurements.first()
        
        context = {
            'workout_plan': workout_plan,
            'client': client,
            'latest_measurement': latest_measurement,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
        }
        
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        else:
            return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def _daily_exercise_date(request):
    """Parse ?date=YYYY-MM-DD; default today (timezone-aware)."""
    raw = request.query_params.get('date')
    if raw:
        try:
            return timezone.datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return timezone.localdate()


class ClientDailyExerciseView(APIView):
    """GET /api/client/me/daily-exercise/?date=YYYY-MM-DD — get or create today's recommendation."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        for_date = _daily_exercise_date(request)
        rec = generate_daily_recommendation(client, for_date=for_date)
        serializer = DailyExerciseRecommendationSerializer(rec)
        return Response(serializer.data)


class ClientDailyExerciseCompleteView(APIView):
    """POST /api/client/me/daily-exercise/<id>/complete/ — mark completed + post-workout (closed-loop V1.1)."""
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, pk):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        rec = DailyExerciseRecommendation.objects.filter(
            id=pk,
            client=client,
        ).select_related('exercise').first()
        if not rec:
            return Response(
                {'error': 'Recomendación no encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Request body: post-workout metrics (required for closed-loop)
        body_serializer = CompleteDailyExerciseSerializer(data=request.data or {})
        if not body_serializer.is_valid():
            return Response(body_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = body_serializer.validated_data

        rec.status = DailyExerciseRecommendation.Status.COMPLETED
        rec.save(update_fields=['status'])

        # Resolve executed exercise
        executed_exercise_id = data.get('executed_exercise_id')
        if executed_exercise_id:
            executed_exercise = Exercise.objects.filter(id=executed_exercise_id).first()
        else:
            executed_exercise = rec.exercise

        # Snapshot progression state before (for audit)
        state = get_or_create_progression_state(client)
        progression_before = {
            'current_load_score': state.current_load_score,
            'intensity_bias': state.intensity_bias,
            'high_days_streak': state.high_days_streak,
            'cooldown_days_remaining': state.cooldown_days_remaining,
        }

        # Create or update TrainingLog (one per client per date)
        log, created = TrainingLog.objects.update_or_create(
            client=client,
            date=rec.date,
            defaults={
                'suggested_exercise': rec.exercise,
                'executed_exercise': executed_exercise,
                'execution_status': TrainingLog.ExecutionStatus.DONE,
                'rpe': data['rpe'],
                'energy_level': data['energy_level'],
                'pain_level': data['pain_level'],
                'notes': data.get('notes') or '',
                'recommendation_version': 'daily_exercise_v1.1',
                'recommendation_meta': {
                    'rec_id': rec.id,
                    'rec_date': str(rec.date),
                    'rec_type': rec.type,
                    'rec_intensity': rec.intensity,
                    'rules_applied': rec.metadata.get('applied_rules', []),
                    'progression_before': progression_before,
                },
            },
        )
        # Update meta with progression_after after we run progression
        outcome = evaluate_outcome(log)
        state, delta, message = apply_progression_update(state, outcome)
        log.recommendation_meta['progression_after'] = {
            'current_load_score': state.current_load_score,
            'intensity_bias': state.intensity_bias,
        }
        log.save(update_fields=['recommendation_meta'])

        progression_update = {
            'outcome_score': outcome.outcome_score,
            'flags': outcome.flags,
            'intensity_bias_before': delta['intensity_bias_before'],
            'intensity_bias_after': delta['intensity_bias_after'],
            'message': message,
        }

        rec_serializer = DailyExerciseRecommendationSerializer(rec)
        return Response({
            'recommendation': rec_serializer.data,
            'training_log_id': log.id,
            'progression_update': progression_update,
        })


