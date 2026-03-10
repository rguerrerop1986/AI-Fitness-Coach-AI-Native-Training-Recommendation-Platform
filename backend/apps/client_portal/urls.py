from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.plans.views import ClientCurrentCycleView
from apps.appointments.views import ClientAppointmentView
from apps.tracking.views import ClientTrainingLogMeView, ClientDietLogMeView
from .views import (
    ClientDashboardView,
    ClientReadinessTodayView,
    ClientPlanViewSet,
    ClientCurrentPlanView,
    ClientPlanPDFView,
    ClientDailyExerciseView,
    ClientDailyExerciseCompleteView,
)

router = DefaultRouter()
router.register(r'plans', ClientPlanViewSet, basename='client-plan')

urlpatterns = [
    # Client portal endpoints (auth is handled by unified /api/auth/token/client/)
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('readiness/today/', ClientReadinessTodayView.as_view(), name='client-readiness-today'),
    path('current-cycle/', ClientCurrentCycleView.as_view(), name='client-current-cycle'),
    path('current-plan/', ClientCurrentPlanView.as_view(), name='client-current-plan'),
    path('current-plan/pdf/', ClientPlanPDFView.as_view(), name='client-plan-pdf'),
    path('me/appointments/', ClientAppointmentView.as_view(), name='client-appointments'),
    path('me/training-log/', ClientTrainingLogMeView.as_view(), name='client-me-training-log'),
    path('me/diet-log/', ClientDietLogMeView.as_view(), name='client-me-diet-log'),
    path('me/daily-exercise/', ClientDailyExerciseView.as_view(), name='client-me-daily-exercise'),
    path('me/daily-exercise/<int:pk>/complete/', ClientDailyExerciseCompleteView.as_view(), name='client-me-daily-exercise-complete'),
    path('', include(router.urls)),
]
