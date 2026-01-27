import os
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import get_template
from django.template import Context

from .models import ClientSubscription, ClientAccessLog
from .serializers import (
    ClientSubscriptionSerializer, ClientLoginSerializer,
    ClientDashboardSerializer, DietPlanDetailSerializer, WorkoutPlanDetailSerializer
)
from apps.clients.models import Client
from apps.plans.models import DietPlan, WorkoutPlan, PlanAssignment


class ClientLoginView(APIView):
    """Client login endpoint."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ClientLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            try:
                subscription = ClientSubscription.objects.get(username=username)
                
                if not subscription.is_active:
                    return Response({
                        'error': 'Subscription is not active'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                if not check_password(password, subscription.password_hash):
                    return Response({
                        'error': 'Invalid credentials'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                # Update last login
                subscription.last_login = timezone.now()
                subscription.save()
                
                # Log access
                ClientAccessLog.objects.create(
                    client=subscription.client,
                    action='login',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Generate JWT token
                refresh = RefreshToken()
                refresh['client_id'] = subscription.client.id
                refresh['username'] = subscription.username
                refresh['role'] = 'client'
                
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'client': {
                        'id': subscription.client.id,
                        'name': subscription.client.full_name,
                        'email': subscription.client.email,
                    }
                })
                
            except ClientSubscription.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ClientDashboardView(APIView):
    """Client dashboard endpoint."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get client from token
        client_id = request.user.get('client_id')
        if not client_id:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            client = Client.objects.get(id=client_id)
            serializer = ClientDashboardSerializer(client)
            return Response(serializer.data)
        except Client.DoesNotExist:
            return Response({
                'error': 'Client not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ClientPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for client plan access."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        client_id = self.request.user.get('client_id')
        if not client_id:
            return PlanAssignment.objects.none()
        
        return PlanAssignment.objects.filter(
            client_id=client_id,
            is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def diet_plan_detail(self, request, pk=None):
        """Get detailed diet plan information."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'diet' or not assignment.diet_plan:
            return Response({
                'error': 'No diet plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log access
        ClientAccessLog.objects.create(
            client=assignment.client,
            action='view_plan',
            plan_type='diet',
            plan_id=assignment.diet_plan.id,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = DietPlanDetailSerializer(assignment.diet_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def workout_plan_detail(self, request, pk=None):
        """Get detailed workout plan information."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'workout' or not assignment.workout_plan:
            return Response({
                'error': 'No workout plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log access
        ClientAccessLog.objects.create(
            client=assignment.client,
            action='view_plan',
            plan_type='workout',
            plan_id=assignment.workout_plan.id,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = WorkoutPlanDetailSerializer(assignment.workout_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download_diet_pdf(self, request, pk=None):
        """Download diet plan as PDF."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'diet' or not assignment.diet_plan:
            return Response({
                'error': 'No diet plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log download
        ClientAccessLog.objects.create(
            client=assignment.client,
            action='download_pdf',
            plan_type='diet',
            plan_id=assignment.diet_plan.id,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Generate PDF
        pdf_content = self.generate_diet_pdf(assignment.diet_plan, assignment.client)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="diet_plan_{assignment.diet_plan.title.replace(" ", "_")}.pdf"'
        return response
    
    @action(detail=True, methods=['get'])
    def download_workout_pdf(self, request, pk=None):
        """Download workout plan as PDF."""
        assignment = self.get_object()
        
        if assignment.plan_type != 'workout' or not assignment.workout_plan:
            return Response({
                'error': 'No workout plan assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log download
        ClientAccessLog.objects.create(
            client=assignment.client,
            action='download_pdf',
            plan_type='workout',
            plan_id=assignment.workout_plan.id,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Generate PDF
        pdf_content = self.generate_workout_pdf(assignment.workout_plan, assignment.client)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="workout_plan_{assignment.workout_plan.title.replace(" ", "_")}.pdf"'
        return response
    
    def generate_diet_pdf(self, diet_plan, client):
        """Generate PDF for diet plan."""
        template = get_template('client_portal/diet_plan_pdf.html')
        
        # Get latest measurement
        latest_measurement = client.measurements.first()
        
        context = {
            'diet_plan': diet_plan,
            'client': client,
            'latest_measurement': latest_measurement,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
        }
        
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        else:
            return None
    
    def generate_workout_pdf(self, workout_plan, client):
        """Generate PDF for workout plan."""
        template = get_template('client_portal/workout_plan_pdf.html')
        
        # Get latest measurement
        latest_measurement = client.measurements.first()
        
        context = {
            'workout_plan': workout_plan,
            'client': client,
            'latest_measurement': latest_measurement,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
        }
        
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return result.getvalue()
        else:
            return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ClientSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing client subscriptions (admin only)."""
    queryset = ClientSubscription.objects.all()
    serializer_class = ClientSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Hash the password before saving
        if 'password' in self.request.data:
            password = self.request.data['password']
            serializer.save(password_hash=make_password(password))
        else:
            serializer.save()
