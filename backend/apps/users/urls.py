from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import LoginView, RegisterView, UserProfileView, logout, refresh_token
from .serializers import ClientTokenObtainPairSerializer

app_name = 'users'


urlpatterns = [
    # Standard SimpleJWT endpoints (unified auth for all users)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Client portal specific endpoint (uses custom serializer to validate client role)
    path('auth/token/client/', TokenObtainPairView.as_view(serializer_class=ClientTokenObtainPairSerializer), name='client_token_obtain'),
    
    # Legacy endpoints (kept for backwards compatibility)
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', logout, name='logout'),
    path('auth/refresh/', refresh_token, name='refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
