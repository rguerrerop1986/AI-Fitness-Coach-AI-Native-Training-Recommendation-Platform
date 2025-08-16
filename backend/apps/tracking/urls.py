from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tracking'

router = DefaultRouter()
router.register(r'check-ins', views.CheckInViewSet, basename='checkin')
router.register(r'reports', views.ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
