from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.plans.views import ClientCurrentCycleView
from apps.appointments.views import ClientAppointmentView
from .views import (
    ClientDashboardView, ClientPlanViewSet
)

router = DefaultRouter()
router.register(r'plans', ClientPlanViewSet, basename='client-plan')

urlpatterns = [
    # Client portal endpoints (auth is handled by unified /api/auth/token/client/)
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('current-cycle/', ClientCurrentCycleView.as_view(), name='client-current-cycle'),
    path('me/appointments/', ClientAppointmentView.as_view(), name='client-appointments'),
    path('', include(router.urls)),
]
