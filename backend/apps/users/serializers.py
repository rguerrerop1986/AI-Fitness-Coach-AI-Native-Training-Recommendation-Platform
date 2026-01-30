from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.clients.models import Client
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']
        read_only_fields = ['id']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password.')
        
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class ClientTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer for clients that validates client role and linked Client profile.
    Accepts email in the username field: if input contains '@', look up User by email (client only).
    """
    
    def validate(self, attrs):
        username_or_email = (attrs.get('username') or '').strip()
        if '@' in username_or_email:
            try:
                user = User.objects.get(email__iexact=username_or_email, role='client')
                attrs = {**attrs, 'username': user.username}
            except User.DoesNotExist:
                pass
        # Call parent validation to authenticate user
        data = super().validate(attrs)
        
        # Check if user is a client
        if self.user.role != 'client':
            raise serializers.ValidationError('Only clients can access the client portal.')
        
        # Check if client has a linked Client record
        try:
            client = Client.objects.get(user=self.user)
        except Client.DoesNotExist:
            raise serializers.ValidationError('Client profile not found. Please contact your coach.')
        
        # Log login access (request is automatically in context from TokenObtainPairView)
        try:
            from apps.client_portal.models import ClientAccessLog
            
            request = self.context.get('request')
            ip_address = None
            user_agent = ''
            
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR', None)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            ClientAccessLog.objects.create(
                client=client,
                action='login',
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception:
            # Don't fail login if logging fails
            pass
        
        # Add client info to response
        data['client'] = {
            'id': client.id,
            'name': client.full_name,
            'email': client.email,
        }
        
        return data
