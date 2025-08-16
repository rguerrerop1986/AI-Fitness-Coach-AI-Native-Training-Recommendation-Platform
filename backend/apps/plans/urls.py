from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'plans'

router = DefaultRouter()
router.register(r'diet-plans', views.DietPlanViewSet)
router.register(r'workout-plans', views.WorkoutPlanViewSet)
router.register(r'assignments', views.PlanAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
