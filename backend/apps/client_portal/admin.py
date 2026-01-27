from django.contrib import admin
from .models import ClientAccessLog


@admin.register(ClientAccessLog)
class ClientAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'action', 'plan_type', 'plan_id', 'ip_address', 'created_at'
    ]
    list_filter = ['action', 'plan_type', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'client__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Action Details', {
            'fields': ('action', 'plan_type', 'plan_id')
        }),
        ('Access Information', {
            'fields': ('ip_address', 'user_agent', 'created_at')
        }),
    )
