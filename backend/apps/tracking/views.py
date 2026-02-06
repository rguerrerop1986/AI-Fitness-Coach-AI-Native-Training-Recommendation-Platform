from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from apps.common.permissions import IsCoachOrAssistant, IsClient, get_client_from_user
from .models import CheckIn, TrainingLog, DietLog
from .serializers import (
    CheckInSerializer, CheckInCreateSerializer,
    TrainingLogSerializer, DietLogSerializer,
)


class CheckInViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing client check-ins (coach only).
    """
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filterset_fields = ['client', 'date']
    search_fields = ['notes']
    
    def get_queryset(self):
        """Filter check-ins by client if client_id is provided in URL."""
        queryset = CheckIn.objects.select_related('client').all()
        client_id = self.kwargs.get('client_pk')
        if client_id is not None:
            queryset = queryset.filter(client_id=client_id)
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return CheckInCreateSerializer
        return CheckInSerializer

    def create(self, request, *args, **kwargs):
        """Create check-in; response uses CheckInSerializer for full payload."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_id = kwargs.get('client_pk')
        if client_id:
            from apps.clients.models import Client
            client = Client.objects.get(id=client_id)
            if not client.is_active:
                return Response(
                    {'detail': 'El cliente está inactivo. No se pueden crear seguimientos.'},
                    status=status.HTTP_409_CONFLICT,
                )
            instance = serializer.save(client=client)
        else:
            # Standalone create (e.g. POST /api/tracking/check-ins/ with client_id in body)
            client_id = serializer.validated_data.get('client_id')
            if client_id is not None:
                from apps.clients.models import Client
                c = Client.objects.filter(pk=client_id).first()
                if c and not c.is_active:
                    return Response(
                        {'detail': 'El cliente está inactivo. No se pueden crear seguimientos.'},
                        status=status.HTTP_409_CONFLICT,
                    )
            instance = serializer.save()
        return Response(
            CheckInSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        """Legacy: set client when creating (used if create() not overridden)."""
        client_id = self.kwargs.get('client_pk')
        if client_id:
            from apps.clients.models import Client
            client = Client.objects.get(id=client_id)
            serializer.save(client=client)
        else:
            serializer.save()


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for generating reports (coach only).
    """
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    
    def get_queryset(self):
        # This will be implemented later with actual report logic
        return CheckIn.objects.none()


# ---- Coach API: TrainingLog & DietLog (full CRUD, filters) ----

class TrainingLogViewSet(viewsets.ModelViewSet):
    """Coach: CRUD training logs. Filters: client, date, date_from, date_to, plan_cycle."""
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    serializer_class = TrainingLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'date', 'plan_cycle']

    def get_queryset(self):
        qs = TrainingLog.objects.select_related(
            'client', 'plan_cycle', 'coach',
            'suggested_exercise', 'executed_exercise',
        ).all()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs


class DietLogViewSet(viewsets.ModelViewSet):
    """Coach: CRUD diet logs. Filters: client, date, date_from, date_to, plan_cycle."""
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    serializer_class = DietLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client', 'date', 'plan_cycle']

    def get_queryset(self):
        qs = DietLog.objects.select_related('client', 'plan_cycle', 'coach').all()
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs


# ---- AI Coach Dashboard (coach-only, JWT auth) ----

class CoachDashboardView(APIView):
    """GET /api/tracking/coach-dashboard/?days=7 — summary for current coach (high pain, not_done streaks, adherence, by_client)."""
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]

    def get(self, request):
        try:
            days = int(request.query_params.get('days', 7))
            days = min(max(1, days), 90)
        except (TypeError, ValueError):
            days = 7
        coach_id = request.user.id
        end_date = timezone.localdate() + timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        logs = TrainingLog.objects.filter(
            plan_cycle__coach_id=coach_id,
            date__gte=start_date,
            date__lt=end_date,
        ).select_related('client', 'suggested_exercise', 'executed_exercise', 'plan_cycle').order_by('-date')

        client_ids = list(logs.values_list('client_id', flat=True).distinct())
        high_pain_clients = []
        not_done_streak_clients = []
        by_client = {}

        for log in logs:
            cid = log.client_id
            if cid not in by_client:
                by_client[cid] = {'client_id': cid, 'client_name': log.client.full_name, 'logs': [], 'risk_score': 0}
            by_client[cid]['logs'].append(TrainingLogSerializer(log).data)

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
            # Simple risk score: high pain + low adherence
            total = len(client_logs)
            completed = sum(1 for l in client_logs if l.execution_status in (TrainingLog.ExecutionStatus.DONE, TrainingLog.ExecutionStatus.PARTIAL))
            adherence = (completed / total) if total else 0
            risk = 0
            if last and (last.pain_level or 0) >= 6:
                risk += 40
            if adherence < 0.5:
                risk += 30
            if not_done_count >= 2:
                risk += 30
            by_client[cid]['risk_score'] = min(100, risk)

        adherence_trend = []
        for cid in client_ids:
            client_logs = [l for l in logs if l.client_id == cid]
            completed = sum(1 for l in client_logs if l.execution_status in (TrainingLog.ExecutionStatus.DONE, TrainingLog.ExecutionStatus.PARTIAL))
            total = len(client_logs)
            rate = round(completed / total, 2) if total else 0
            adherence_trend.append({'client_id': cid, 'client_name': by_client[cid]['client_name'], 'adherence_rate': rate, 'logs_count': total})

        return Response({
            'coach_id': coach_id,
            'days': days,
            'high_pain_clients': high_pain_clients,
            'not_done_streak_clients': not_done_streak_clients,
            'adherence_trend': adherence_trend,
            'by_client': list(by_client.values()),
        })


# ---- Client "me" endpoints: single log per date (upsert) ----

def _log_date(request):
    """Parse ?date=YYYY-MM-DD; default today."""
    raw = request.query_params.get('date') or request.data.get('date')
    if raw:
        try:
            return timezone.datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return timezone.localdate()


class ClientTrainingLogMeView(APIView):
    """GET/POST/PATCH /api/client/me/training-log/?date=YYYY-MM-DD — client's own log only."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        log_date = _log_date(request)
        log = TrainingLog.objects.filter(client=client, date=log_date).select_related(
            'suggested_exercise', 'executed_exercise'
        ).first()
        if not log:
            return Response({'data': None})
        return Response({'data': TrainingLogSerializer(log).data})

    def post(self, request):
        """Create or update (upsert) training log for the given date."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        log_date = _log_date(request)
        # Ignore client_id from body
        data = {k: v for k, v in request.data.items() if k != 'client' and k != 'client_id'}
        data['client'] = client.id
        data['date'] = log_date
        log = TrainingLog.objects.filter(client=client, date=log_date).first()
        if log:
            serializer = TrainingLogSerializer(log, data=data, partial=True)
        else:
            serializer = TrainingLogSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=client, date=log_date)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        return self.post(request)


class ClientDietLogMeView(APIView):
    """GET/POST/PATCH /api/client/me/diet-log/?date=YYYY-MM-DD — client's own log only."""
    permission_classes = [IsAuthenticated, IsClient]

    def get(self, request):
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        log_date = _log_date(request)
        log = DietLog.objects.filter(client=client, date=log_date).first()
        if not log:
            return Response({'data': None})
        return Response({'data': DietLogSerializer(log).data})

    def post(self, request):
        """Create or update (upsert) diet log for the given date."""
        client = get_client_from_user(request.user)
        if not client:
            return Response(
                {'error': 'Client profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        log_date = _log_date(request)
        data = {k: v for k, v in request.data.items() if k != 'client' and k != 'client_id'}
        data['client'] = client.id
        data['date'] = log_date
        log = DietLog.objects.filter(client=client, date=log_date).first()
        if log:
            serializer = DietLogSerializer(log, data=data, partial=True)
        else:
            serializer = DietLogSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=client, date=log_date)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        return self.post(request)
