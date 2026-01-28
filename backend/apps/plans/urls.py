from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'plans'

router = DefaultRouter()
router.register(r'diet-plans', views.DietPlanViewSet)
router.register(r'workout-plans', views.WorkoutPlanViewSet)
router.register(r'assignments', views.PlanAssignmentViewSet)
router.register(r'plan-cycles', views.PlanCycleViewSet, basename='plan-cycle')
router.register(r'training-entries', views.TrainingEntryViewSet, basename='training-entry')
router.register(r'meals', views.MealViewSet, basename='meal')

urlpatterns = [
    path('', include(router.urls)),
]
