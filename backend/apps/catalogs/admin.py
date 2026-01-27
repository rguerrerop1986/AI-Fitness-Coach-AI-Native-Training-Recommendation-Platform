from django.contrib import admin
from .models import Food, Exercise


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'kcal', 'protein_g', 'carbs_g', 'fat_g', 'is_active']
    list_filter = ['is_active', 'tags', 'created_at']
    search_fields = ['name', 'brand']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'serving_size')
        }),
        ('Nutritional Information', {
            'fields': ('kcal', 'protein_g', 'carbs_g', 'fat_g')
        }),
        ('Categorization', {
            'fields': ('tags',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'difficulty', 'equipment', 'is_active']
    list_filter = ['muscle_group', 'difficulty', 'is_active', 'created_at']
    search_fields = ['name', 'muscle_group', 'equipment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['muscle_group', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'muscle_group', 'difficulty', 'equipment')
        }),
        ('Instructions', {
            'fields': ('instructions',)
        }),
        ('Media', {
            'fields': ('video_url',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
