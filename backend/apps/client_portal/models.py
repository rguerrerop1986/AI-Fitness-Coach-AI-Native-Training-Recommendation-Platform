from django.db import models
from apps.clients.models import Client


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
