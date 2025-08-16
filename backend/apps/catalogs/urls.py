from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FoodViewSet, ExerciseViewSet

router = DefaultRouter()
router.register(r'foods', FoodViewSet)
router.register(r'exercises', ExerciseViewSet)

app_name = 'catalogs'

urlpatterns = [
    path('', include(router.urls)),
]
