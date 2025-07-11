  # apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds role-based access control and additional user information.
    Username, email and password are required
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('external', 'External Client'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='external',
        help_text="User role determines access permissions"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Contact phone number"
    )
    organization = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Organization or company name"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_staff_member(self):
        return self.role in ['admin', 'staff']
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username