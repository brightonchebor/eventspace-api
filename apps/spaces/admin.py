# Register your models here.
from django.contrib import admin
from .models import Space

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'status', 'created_at', 'price_per_hour']
    list_filter = ['status', 'created_at', 'capacity']
    search_fields = ['name', 'location', 'description']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'capacity', 'status', 'price_per_hour')
        }),
        ('Images', {
            'fields': ('image1', 'image2', 'image3', 'image4', 'image5'),
            'classes': ('collapse',)
        }),
        ('Details', {
            'fields': ('description', 'equipment', 'features'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
