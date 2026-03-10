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
    ClientDashboardSerializer,
    ClientDashboardV2Serializer,
    DietPlanDetailSerializer,
    WorkoutPlanDetailSerializer,
    DailyExerciseRecommendationSerializer,
    CompleteDailyExerciseSerializer,
    DailyReadinessCheckinSerializer,
)
from apps.clients.models import Client
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment, PlanCycle
from apps.plans.serializers import PlanAssignmentSerializer, ClientPlanCycleSerializer
from apps.common.permissions import IsClient, get_client_from_user
from apps.tracking.models import (
    DailyExerciseRecommendation,
    TrainingLog,
    DailyReadinessCheckin,
    DailyTrainingRecommendation,
    DailyDietRecommendation,
)
from apps.client_portal.services.daily_recommendation_service import (
    get_or_create_daily_recommendation,
    InsufficientCatalogError,
    ensure_training_group,
)
from apps.catalogs.models import Exercise
from apps.recommendations.services.daily_exercise import generate_daily_recommendation
from apps.recommendations.services.progression import (
    evaluate_outcome,
    apply_progression_update,
    get_or_create_progression_state,
)
from django.http import FileResponse
import logging

logger = logging.getLogger(__name__)


def _build_dashboard_v2_payload(client, today, training_rec, diet_rec, readiness=None, readiness_required=False):
    """Build dashboard V2 payload: client, today, diet_plan_active, training_plan_active, readiness state."""
    # Current weight: latest measurement or initial_weight_kg; allow null
    latest = client.measurements.first()
    current_weight = None
    if latest and latest.weight_kg is not None:
        current_weight = float(latest.weight_kg)
    elif client.initial_weight_kg is not None:
        current_weight = float(client.initial_weight_kg)

    # Height in cm (backend stores height_m); never break on missing
    height_cm = None
    if client.height_m is not None:
        try:
            height_cm = int(round(float(client.height_m) * 100))
        except (TypeError, ValueError):
            pass

    payload = {
        'client': {
            'id': client.id,
            'name': client.full_name,
            'current_weight': current_weight,
            'height_cm': height_cm,
        },
        'today': today.isoformat(),
        'diet_plan_active': None,
        'training_plan_active': None,
        'readiness_required': readiness_required,
        'has_today_readiness': readiness is not None,
        'readiness': DailyReadinessCheckinSerializer(readiness).data if readiness else None,
        'has_recommendation_today': bool(training_rec or diet_rec),
    }

    if diet_rec:
        meals_list = []
        for m in sorted(diet_rec.meals.all(), key=lambda x: x.order):
            foods_list = []
            meal_foods_q = getattr(m, 'meal_foods', None)
            meal_foods_list = sorted(meal_foods_q.all(), key=lambda x: x.order) if meal_foods_q else []
            for mf in meal_foods_list:
                f = mf.food
                qty = float(mf.quantity) if mf.quantity else 1
                unit = mf.unit or 'g'
                calories = None
                if getattr(f, 'calories_kcal', None) is not None and getattr(f, 'serving_size', None):
                    try:
                        calories = int(float(f.calories_kcal or 0) * float(qty) / 100)
                    except (TypeError, ValueError):
                        pass
                if calories is None and getattr(f, 'kcal', None) is not None and getattr(f, 'serving_size', None):
                    try:
                        calories = int(float(f.kcal or 0) * float(qty) / float(f.serving_size))
                    except (TypeError, ValueError, ZeroDivisionError):
                        pass
                foods_list.append({
                    'id': f.id,
                    'name': f.name,
                    'quantity': qty,
                    'unit': unit,
                    'calories': calories,
                })
            meals_list.append({
                'meal_type': m.meal_type,
                'title': m.title or m.get_meal_type_display(),
                'foods': foods_list,
            })
        payload['diet_plan_active'] = {
            'title': diet_rec.title or 'Plan diario personalizado',
            'goal': diet_rec.goal or 'Mantenimiento',
            'coach_message': diet_rec.coach_message or '',
            'total_calories': diet_rec.total_calories,
            'meals': meals_list,
        }

    if training_rec:
        # Backwards compatibility: derive training_group when falta en registros antiguos
        training_rec = ensure_training_group(training_rec)
        video_data = None
        if training_rec.recommended_video:
            v = training_rec.recommended_video
            video_data = {
                'title': v.name,
                'duration_minutes': v.duration_minutes,
            }
        ordered_exercises = sorted(training_rec.exercises.all(), key=lambda e: e.order)
        exercises_data = [
            {
                'name': e.exercise.name,
                'sets': e.sets,
                'reps': e.reps,
                'order': e.order,
                'rest_seconds': e.rest_seconds,
                'notes': e.notes or '',
            }
            for e in ordered_exercises
        ]
        training_group = getattr(training_rec, 'training_group', '') or ''
        training_group_label = (
            training_rec.get_training_group_display()
            if training_group and hasattr(training_rec, 'get_training_group_display')
            else ''
        )
        payload['training_plan_active'] = {
            'recommendation_type': training_rec.recommendation_type,
            'training_group': training_group,
            'training_group_label': training_group_label,
            'modality': getattr(training_rec, 'modality', '') or '',
            'intensity_level': getattr(training_rec, 'intensity_level', None),
            'reasoning_summary': training_rec.reasoning_summary or '',
            'coach_message': training_rec.coach_message or '',
            'recommended_video': video_data,
            'exercises': exercises_data,
        }

    return payload


class ClientDashboardView(APIView):
    """Client dashboard. GET: Caso A sin check-in -> readiness_required; B/C con check-in -> recomendación IA o existente."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.localdate()
        readiness = DailyReadinessCheckin.objects.filter(client=client, date=today).first()

        # Caso A: no hay check-in del día -> no generar recomendación aún
        if not readiness:
            training_rec = DailyTrainingRecommendation.objects.filter(client=client, date=today).first()
            diet_rec = DailyDietRecommendation.objects.filter(client=client, date=today).first()
            payload = _build_dashboard_v2_payload(
                client, today, training_rec, diet_rec,
                readiness=None,
                readiness_required=True,
            )
            serializer = ClientDashboardV2Serializer(data=payload)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data)

        # Caso B/C: hay check-in -> si no hay recomendación, generar con IA
        training_rec = DailyTrainingRecommendation.objects.filter(client=client, date=today).first()
        diet_rec = DailyDietRecommendation.objects.filter(client=client, date=today).first()

        if not training_rec and not diet_rec:
            try:
                from apps.client_portal.services.ai_daily_plan import generate_ai_daily_plan
                training_rec, diet_rec = generate_ai_daily_plan(client, readiness, target_date=today)
            except Exception as e:
                logger.warning("Failed to generate AI daily plan: %s", e, exc_info=True)
            if not training_rec and not diet_rec:
                try:
                    training_rec, diet_rec = get_or_create_daily_recommendation(client, target_date=today)
                except InsufficientCatalogError as e:
                    return Response(
                        {
                            'error': 'insufficient_catalog',
                            'detail': str(e),
                            'catalog': e.catalog,
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )

        payload = _build_dashboard_v2_payload(
            client, today, training_rec, diet_rec,
            readiness=readiness,
            readiness_required=False,
        )
        serializer = ClientDashboardV2Serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class ClientReadinessTodayView(APIView):
    """GET/POST /api/client/readiness/today/ — get or create/update today's readiness check-in."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        today = timezone.localdate()
        readiness = DailyReadinessCheckin.objects.filter(client=client, date=today).first()
        data = {
            'today': today.isoformat(),
            'has_today_readiness': readiness is not None,
            'readiness': DailyReadinessCheckinSerializer(readiness).data if readiness else None,
        }
        return Response(data)

    def post(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found. Please contact your coach.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        today = timezone.localdate()
        body = dict(request.data or {})
        body['date'] = today
        existing = DailyReadinessCheckin.objects.filter(client=client, date=today).first()
        serializer = DailyReadinessCheckinSerializer(
            existing,
            data=body,
            partial=bool(existing),
            context={'client': client},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(DailyReadinessCheckinSerializer(instance).data, status=status.HTTP_200_OK)


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


class ClientDailyExerciseView(APIView):
    """GET /api/client/me/daily-exercise/ — get or create today's recommendation (server date, TIME_ZONE)."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        today = timezone.localdate()
        rec = generate_daily_recommendation(client, for_date=today)
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
        state, delta, message = apply_progression_update(state, outcome, log_date=rec.date)
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


