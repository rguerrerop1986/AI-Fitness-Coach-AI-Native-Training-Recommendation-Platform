from django.db import models
from django.contrib.auth import get_user_model
from apps.clients.models import Client

User = get_user_model()


class ClientSubscription(models.Model):
    """Client subscription model for accessing the portal."""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'
        PENDING = 'pending', 'Pending'
    
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)  # Store hashed password
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    subscription_start = models.DateField()
    subscription_end = models.DateField()
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.status}"
    
    @property
    def is_active(self):
        from datetime import date
        return self.status == self.Status.ACTIVE and self.subscription_end >= date.today()


class ClientAccessLog(models.Model):
    """Log client access to plans and downloads."""
    
    class Action(models.TextChoices):
        VIEW_PLAN = 'view_plan', 'View Plan'
        DOWNLOAD_PDF = 'download_pdf', 'Download PDF'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    action = models.CharField(max_length=15, choices=Action.choices)
    plan_type = models.CharField(max_length=10, blank=True)  # 'diet' or 'workout'
    plan_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'client_access_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.get_action_display()} - {self.created_at}"
