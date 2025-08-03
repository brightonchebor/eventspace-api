# Register your models here.
from django.contrib import admin
from .models import Space, Review

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'status', 'created_at', 'price_per_day']
    list_filter = ['status', 'created_at', 'capacity']
    search_fields = ['name', 'location', 'description']
    list_editable = ['status']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'capacity', 'status', 'price_per_day')
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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['space', 'user', 'rating', 'created_at', 'short_comment']
    list_filter = ['rating', 'created_at', 'space']
    search_fields = ['comment', 'user__email', 'space__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def short_comment(self, obj):
        """Truncate comment text for display in list view"""
        if len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment
    short_comment.short_description = 'Comment'
