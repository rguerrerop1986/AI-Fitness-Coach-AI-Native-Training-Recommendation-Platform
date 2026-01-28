from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'client', 'coach', 'scheduled_at', 'duration_minutes',
        'status', 'price', 'currency', 'payment_status', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'currency', 'created_at', 'scheduled_at']
    search_fields = ['client__first_name', 'client__last_name', 'client__email', 'coach__username']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'scheduled_at'
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('client', 'coach', 'scheduled_at', 'duration_minutes', 'status', 'notes')
        }),
        ('Payment Information', {
            'fields': ('price', 'currency', 'payment_status', 'payment_method', 'paid_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
