from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from apps.common.permissions import IsCoachOrAssistant
from .models import Food, Exercise
from .serializers import (
    FoodSerializer, ExerciseSerializer, 
    FoodSearchSerializer, ExerciseSearchSerializer
)


class FoodViewSet(viewsets.ModelViewSet):
    """ViewSet for food catalog management (coach only)."""
    queryset = Food.objects.filter(is_active=True)
    serializer_class = FoodSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tags']
    search_fields = ['name', 'brand']
    ordering_fields = ['name', 'kcal', 'protein_g']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(brand__icontains=search) |
                Q(tags__contains=[search])
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search foods with simplified response."""
        queryset = self.get_queryset()
        serializer = FoodSearchSerializer(queryset, many=True)
        return Response(serializer.data)


class ExerciseViewSet(viewsets.ModelViewSet):
    """ViewSet for exercise catalog management (coach only)."""
    queryset = Exercise.objects.filter(is_active=True)
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsCoachOrAssistant]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['muscle_group', 'difficulty', 'equipment']
    search_fields = ['name', 'muscle_group', 'equipment']
    ordering_fields = ['name', 'muscle_group', 'difficulty']
    ordering = ['muscle_group', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(muscle_group__icontains=search) |
                Q(equipment__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search exercises with simplified response."""
        queryset = self.get_queryset()
        serializer = ExerciseSearchSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def muscle_groups(self, request):
        """Get list of available muscle groups."""
        muscle_groups = Exercise.MuscleGroup.choices
        return Response([{'value': value, 'label': label} for value, label in muscle_groups])
    
    @action(detail=False, methods=['get'])
    def difficulties(self, request):
        """Get list of available difficulty levels."""
        difficulties = Exercise.Difficulty.choices
        return Response([{'value': value, 'label': label} for value, label in difficulties])
