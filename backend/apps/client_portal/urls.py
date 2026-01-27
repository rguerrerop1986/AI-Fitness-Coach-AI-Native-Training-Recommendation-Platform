from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientLoginView, ClientDashboardView, ClientPlanViewSet,
    ClientSubscriptionViewSet
)

router = DefaultRouter()
router.register(r'plans', ClientPlanViewSet, basename='client-plan')
router.register(r'subscriptions', ClientSubscriptionViewSet, basename='client-subscription')

urlpatterns = [
    path('auth/login/', ClientLoginView.as_view(), name='client-login'),
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('', include(router.urls)),
]
