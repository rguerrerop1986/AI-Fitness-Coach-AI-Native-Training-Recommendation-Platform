"""
Internal API views (MCP / server-to-server).
All require X-Internal-Token. No JWT.
"""
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.clients.models import Client
from apps.tracking.models import TrainingLog
from apps.catalogs.models import Exercise
from apps.plans.models import PlanCycle
from apps.recommendations.services.training_recommender import suggest_exercise_for_today
from apps.recommendations.selectors import get_recent_training_logs, compute_adherence_rate, compute_pain_trend

from .permissions import InternalTokenPermission
from .serializers import InternalTrainingLogSerializer, InternalExerciseSerializer, exercise_summary


def _parse_date(value):
    if not value:
        return timezone.localdate()
    try:
        return timezone.datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _client_or_404(client_id):
    try:
        return Client.objects.get(pk=client_id)
    except (Client.DoesNotExist, ValueError):
        return None


class SuggestTodayView(APIView):
    """POST /api/internal/recommendations/suggest-today/ { client_id, date? }"""
    permission_classes = [InternalTokenPermission]

    def post(self, request):
        client_id = request.data.get('client_id')
        if not client_id:
            return Response({'error': 'client_id required'}, status=status.HTTP_400_BAD_REQUEST)
        client = _client_or_404(client_id)
        if not client:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        target_date = _parse_date(request.data.get('date'))
        if not target_date:
            return Response({'error': 'date must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        result = suggest_exercise_for_today(client, target_date)
        exercise = result.get('exercise')
        return Response({
            'exercise': exercise_summary(exercise) if exercise else None,
            'rationale': result.get('rationale', ''),
            'meta': result.get('meta', {}),
            'confidence': str(result.get('confidence', 0)),
        }, status=status.HTTP_200_OK)


class TrackingContextView(APIView):
    """GET /api/internal/tracking/context/?client_id=&days=14"""
    permission_classes = [InternalTokenPermission]

    def get(self, request):
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({'error': 'client_id required'}, status=status.HTTP_400_BAD_REQUEST)
        client = _client_or_404(client_id)
        if not client:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            days = int(request.query_params.get('days', 14))
            days = min(max(1, days), 90)
        except (TypeError, ValueError):
            days = 14

        logs = list(get_recent_training_logs(client, days=days).order_by('-date'))
        adherence = compute_adherence_rate(logs)
        pain_trend = compute_pain_trend(logs)
        return Response({
            'client_id': client.id,
            'days': days,
            'logs': InternalTrainingLogSerializer(logs, many=True).data,
            'adherence_rate': adherence,
            'pain_trend': pain_trend,
        }, status=status.HTTP_200_OK)


class TrackingFeedbackView(APIView):
    """POST /api/internal/tracking/feedback/ { client_id, date, execution_status, rpe?, energy_level?, pain_level?, notes?, executed_exercise_id? }"""
    permission_classes = [InternalTokenPermission]

    def post(self, request):
        data = request.data
        client_id = data.get('client_id')
        date_val = _parse_date(data.get('date'))
        if not client_id:
            return Response({'error': 'client_id required'}, status=status.HTTP_400_BAD_REQUEST)
        if not date_val:
            return Response({'error': 'date required (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)
        execution_status = data.get('execution_status')
        if not execution_status:
            return Response({'error': 'execution_status required'}, status=status.HTTP_400_BAD_REQUEST)
        valid_statuses = [c[0] for c in TrainingLog.ExecutionStatus.choices]
        if execution_status not in valid_statuses:
            return Response({'error': f'execution_status must be one of {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        client = _client_or_404(client_id)
        if not client:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        log = TrainingLog.objects.filter(client=client, date=date_val).first()
        if not log:
            log = TrainingLog(client=client, date=date_val)
            cycle = PlanCycle.objects.filter(
                client=client,
                status=PlanCycle.Status.ACTIVE,
                start_date__lte=date_val,
                end_date__gte=date_val,
            ).first()
            if cycle:
                log.plan_cycle = cycle
                log.coach = cycle.coach
            log.save()

        log.execution_status = execution_status
        if 'rpe' in data and data['rpe'] is not None:
            log.rpe = data['rpe']
        if 'energy_level' in data and data['energy_level'] is not None:
            log.energy_level = data['energy_level']
        if 'pain_level' in data and data['pain_level'] is not None:
            log.pain_level = data['pain_level']
        if 'notes' in data:
            log.notes = data['notes'] or ''
        if 'executed_exercise_id' in data and data['executed_exercise_id'] is not None:
            try:
                log.executed_exercise_id = data['executed_exercise_id']
            except (ValueError, Exercise.DoesNotExist):
                log.executed_exercise_id = None
        log.save()
        return Response(InternalTrainingLogSerializer(log).data, status=status.HTTP_200_OK)


class CoachSummaryView(APIView):
    """GET /api/internal/coach/summary/?coach_id=&days=7"""
    permission_classes = [InternalTokenPermission]

    def get(self, request):
        coach_id = request.query_params.get('coach_id')
        if not coach_id:
            return Response({'error': 'coach_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            days = int(request.query_params.get('days', 7))
            days = min(max(1, days), 90)
        except (TypeError, ValueError):
            days = 7

        end_date = timezone.localdate() + timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        # TrainingLogs for this coach's plan_cycles in the window
        logs = TrainingLog.objects.filter(
            plan_cycle__coach_id=coach_id,
            date__gte=start_date,
            date__lt=end_date,
        ).select_related('client', 'suggested_exercise', 'executed_exercise', 'plan_cycle').order_by('-date')

        # Clients with high pain (last log pain_level >= 6)
        client_ids = list(logs.values_list('client_id', flat=True).distinct())
        high_pain_clients = []
        not_done_streak_clients = []
        by_client = {}

        for log in logs:
            cid = log.client_id
            if cid not in by_client:
                by_client[cid] = {'client_id': cid, 'client_name': log.client.full_name, 'logs': [], 'risk_score': 0}
            by_client[cid]['logs'].append(InternalTrainingLogSerializer(log).data)

        # Per-client: last log pain, and count NOT_DONE in last 2
        for cid in client_ids:
            client_logs = [l for l in logs if l.client_id == cid]
            client_logs_sorted = sorted(client_logs, key=lambda x: x.date, reverse=True)
            last = client_logs_sorted[0] if client_logs_sorted else None
            if last and last.pain_level is not None and last.pain_level >= 6:
                high_pain_clients.append({'client_id': cid, 'client_name': last.client.full_name, 'pain_level': last.pain_level})
            recent_two = client_logs_sorted[:2]
            not_done_count = sum(1 for l in recent_two if l.execution_status == TrainingLog.ExecutionStatus.NOT_DONE)
            if not_done_count >= 2:
                not_done_streak_clients.append({'client_id': cid, 'client_name': last.client.full_name if last else ''})

        # Adherence trend: for each client, adherence in window
        adherence_trend = []
        for cid in client_ids:
            client_logs = [l for l in logs if l.client_id == cid]
            completed = sum(1 for l in client_logs if l.execution_status in (TrainingLog.ExecutionStatus.DONE, TrainingLog.ExecutionStatus.PARTIAL))
            total = len(client_logs)
            rate = round(completed / total, 2) if total else 0
            name = by_client[cid]['client_name']
            adherence_trend.append({'client_id': cid, 'client_name': name, 'adherence_rate': rate, 'logs_count': total})

        return Response({
            'coach_id': coach_id,
            'days': days,
            'high_pain_clients': high_pain_clients,
            'not_done_streak_clients': not_done_streak_clients,
            'adherence_trend': adherence_trend,
            'by_client': list(by_client.values()),
        }, status=status.HTTP_200_OK)


class CatalogExercisesView(APIView):
    """GET /api/internal/catalog/exercises/?q=&tags=&limit=20"""
    permission_classes = [InternalTokenPermission]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        tags_param = request.query_params.get('tags', '')
        tags = [t.strip() for t in tags_param.split(',') if t.strip()]
        try:
            limit = min(int(request.query_params.get('limit', 20)), 100)
        except (TypeError, ValueError):
            limit = 20

        qs = Exercise.objects.filter(is_active=True)
        if q:
            qs = qs.filter(name__icontains=q)
        for tag in tags:
            qs = qs.filter(tags__contains=[tag])
        qs = list(qs.order_by('name')[:limit])
        return Response({
            'results': InternalExerciseSerializer(qs, many=True).data,
            'count': len(qs),
        }, status=status.HTTP_200_OK)
