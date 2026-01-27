from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, RegisterView, UserProfileView, logout, refresh_token

app_name = 'users'

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', logout, name='logout'),
    path('auth/refresh/', refresh_token, name='refresh'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
