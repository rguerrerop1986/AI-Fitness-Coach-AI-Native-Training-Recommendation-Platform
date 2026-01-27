from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.plans.views import ClientCurrentCycleView
from .views import (
    ClientTokenObtainPairView, ClientDashboardView, ClientPlanViewSet,
    ClientSubscriptionViewSet
)

router = DefaultRouter()
router.register(r'plans', ClientPlanViewSet, basename='client-plan')
router.register(r'subscriptions', ClientSubscriptionViewSet, basename='client-subscription')

urlpatterns = [
    # New unified auth endpoints (replaces old client login)
    path('auth/token/', ClientTokenObtainPairView.as_view(), name='client-token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='client-token-refresh'),
    # Legacy endpoint (deprecated, kept for backwards compatibility during migration)
    path('auth/login/', ClientTokenObtainPairView.as_view(), name='client-login'),
    path('dashboard/', ClientDashboardView.as_view(), name='client-dashboard'),
    path('current-cycle/', ClientCurrentCycleView.as_view(), name='client-current-cycle'),
    path('', include(router.urls)),
]
