from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import ClientViewSet, MeasurementViewSet
from apps.tracking.views import CheckInViewSet

# Create the main router
router = DefaultRouter()
router.register(r'clients', ClientViewSet)

# Create nested router for measurements
clients_router = routers.NestedDefaultRouter(router, r'clients', lookup='client')
clients_router.register(r'measurements', MeasurementViewSet, basename='client-measurements')
clients_router.register(r'check-ins', CheckInViewSet, basename='client-checkins')

app_name = 'clients'

urlpatterns = [
    path('', include(router.urls)),
    path('', include(clients_router.urls)),
]
