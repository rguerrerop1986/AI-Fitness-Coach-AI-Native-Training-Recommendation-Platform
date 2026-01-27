from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer

User = get_user_model()


class LoginView(generics.GenericAPIView):
    """Login view that returns JWT tokens."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class RegisterView(generics.CreateAPIView):
    """Register view for creating new users."""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    queryset = User.objects.all()


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for getting and updating user profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout view that blacklists the refresh token."""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out.'})
    except Exception:
        return Response({'message': 'Successfully logged out.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token(request):
    """Refresh JWT token."""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            return Response({
                'access': str(token.access_token),
                'refresh': str(token),
            })
        return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Invalid refresh token.'}, status=status.HTTP_400_BAD_REQUEST)
