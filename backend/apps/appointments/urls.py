from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, ClientAppointmentView

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
