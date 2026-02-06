from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Client, Measurement

User = get_user_model()


class MeasurementSerializer(serializers.ModelSerializer):
    """Serializer for client measurements."""
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'date', 'weight_kg', 'body_fat_pct', 'chest_cm', 
            'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for client data."""
    measurements = MeasurementSerializer(many=True, read_only=True)
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    has_portal_access = serializers.SerializerMethodField()
    portal_username = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'date_of_birth',
            'age', 'sex', 'email', 'phone', 'height_m', 'initial_weight_kg',
            'level', 'notes', 'consent_checkbox', 'emergency_contact', 'is_active',
            'deactivated_at', 'deactivated_by', 'deactivation_reason',
            'has_portal_access', 'portal_username',
            'coach', 'measurements', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_has_portal_access(self, obj):
        return obj.user_id is not None

    def get_portal_username(self, obj):
        return obj.user.username if obj.user_id else None


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating clients. Creates a portal User so the client can log in."""
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    coach_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Client
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'sex', 'email',
            'phone', 'height_m', 'initial_weight_kg', 'level', 'notes',
            'consent_checkbox', 'emergency_contact', 'password', 'coach_id',
        ]

    def validate_height_m(self, value):
        if value is None:
            raise serializers.ValidationError('Height (m) is required.')
        val = float(value)
        if val > 10:
            raise serializers.ValidationError(
                'Use height in meters (e.g. 1.85), not centimeters.'
            )
        if val < 0.50 or val > 2.50:
            raise serializers.ValidationError(
                'Height must be between 0.50 and 2.50 m.'
            )
        return value

    def validate_consent_checkbox(self, value):
        if not value:
            raise serializers.ValidationError("Consent checkbox must be checked.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists. Use another email or reset the existing account."
            )
        return value

    def validate_coach_id(self, value):
        if value is None:
            return value
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Coach user not found.")
        if user.role != User.Role.COACH:
            raise serializers.ValidationError("Selected user must have role 'coach'.")
        return value

    def _resolve_coach(self, validated_data, request):
        """Resolve coach: request.user if coach/superuser, else explicit coach_id, else first coach."""
        coach_id = validated_data.pop('coach_id', None)
        if request and (getattr(request.user, 'role', None) == User.Role.COACH or getattr(request.user, 'is_superuser', False)):
            return request.user
        if coach_id is not None:
            coach = User.objects.filter(pk=coach_id, role=User.Role.COACH).first()
            if coach:
                return coach
        return User.objects.filter(role=User.Role.COACH).order_by('id').first()

    def create(self, validated_data):
        password = validated_data.pop('password')
        request = self.context.get('request')
        coach = self._resolve_coach(validated_data, request)
        if coach:
            validated_data['coach'] = coach
        client = Client.objects.create(**validated_data)
        email = client.email
        # Username for portal login: use email so client can log in with email + password
        username = email[:150] if len(email) > 150 else email
        if User.objects.filter(username__iexact=username).exists():
            username = f"client_{client.id}"
        user = User(
            username=username,
            email=email,
            first_name=client.first_name,
            last_name=client.last_name,
            role=User.Role.CLIENT,
        )
        user.set_password(password)
        user.save()
        client.user = user
        client.save(update_fields=['user'])
        return client


class DeactivateClientSerializer(serializers.Serializer):
    """Serializer for deactivate request body (optional reason)."""
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class ClientSetPasswordSerializer(serializers.Serializer):
    """Serializer for setting/updating client portal password."""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters'
    )

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long.')
        return value


class ClientMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for creating measurements for a specific client."""
    
    class Meta:
        model = Measurement
        fields = [
            'date', 'weight_kg', 'body_fat_pct', 'chest_cm', 
            'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm'
        ]
    
    def create(self, validated_data):
        client_id = self.context['client_id']
        validated_data['client_id'] = client_id
        return super().create(validated_data)
