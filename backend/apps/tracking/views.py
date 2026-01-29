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
        queryset = CheckIn.objects.all()
        client_id = self.kwargs.get('client_pk')
        if client_id is not None:
            queryset = queryset.filter(client_id=client_id)
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return CheckInCreateSerializer
        return CheckInSerializer
    
    def perform_create(self, serializer):
        """Set the client when creating a check-in."""
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
