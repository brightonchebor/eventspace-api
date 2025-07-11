# apps/authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    Extends Django's built-in UserAdmin with additional fields.
    """
    
    # Fields to display in the user list
    list_display = (
        'username', 
        'email', 
        'full_name', 
        'role_badge', 
        'organization',
        'is_active',
        'date_joined'
    )
    
    # Fields to filter by
    list_filter = (
        'role', 
        'is_active', 
        'is_staff', 
        'date_joined',
        'organization'
    )
    
    # Fields to search
    search_fields = ('username', 'email', 'first_name', 'last_name', 'organization')
    
    # Default ordering
    ordering = ('-date_joined',)
    
    # Fields layout for the change form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'organization')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields layout for the add form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'role', 'phone', 'organization')
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
    
    def role_badge(self, obj):
        """Display role as a colored badge."""
        colors = {
            'admin': '#dc3545',    # Red
            'staff': '#28a745',    # Green
            'external': '#007bff'  # Blue
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def full_name(self, obj):
        """Display full name or username if name is empty."""
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    # Add actions
    actions = ['make_active', 'make_inactive', 'promote_to_staff']
    
    def make_active(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    make_active.short_description = "Activate selected users"
    
    def make_inactive(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    make_inactive.short_description = "Deactivate selected users"
    
    def promote_to_staff(self, request, queryset):
        """Promote external users to staff."""
        updated = queryset.filter(role='external').update(role='staff')
        self.message_user(request, f'{updated} users promoted to staff.')
    promote_to_staff.short_description = "Promote external users to staff"