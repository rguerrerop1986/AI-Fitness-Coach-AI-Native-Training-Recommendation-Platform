from django.contrib import admin
from .models import Client, Measurement


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'age', 'sex', 'is_active', 'created_at']
    list_filter = ['is_active', 'sex', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'sex', 'email', 'phone')
        }),
        ('Physical Information', {
            'fields': ('height_cm', 'initial_weight_kg')
        }),
        ('Additional Information', {
            'fields': ('notes', 'consent_checkbox', 'emergency_contact')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['client', 'date', 'weight_kg', 'body_fat_pct', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['client__first_name', 'client__last_name']
    readonly_fields = ['created_at']
    ordering = ['-date']
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Measurements', {
            'fields': ('date', 'weight_kg', 'body_fat_pct')
        }),
        ('Body Measurements', {
            'fields': ('chest_cm', 'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
