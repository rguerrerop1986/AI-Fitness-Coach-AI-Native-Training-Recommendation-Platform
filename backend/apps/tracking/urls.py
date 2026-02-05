from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tracking'

router = DefaultRouter()
router.register(r'check-ins', views.CheckInViewSet, basename='checkin')
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'training-logs', views.TrainingLogViewSet, basename='traininglog')
router.register(r'diet-logs', views.DietLogViewSet, basename='dietlog')

urlpatterns = [
    path('coach-dashboard/', views.CoachDashboardView.as_view(), name='coach-dashboard'),
    path('', include(router.urls)),
]
