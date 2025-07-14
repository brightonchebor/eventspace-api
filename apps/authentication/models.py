from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Add extra fields as needed for authentication and roles.
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('external', 'External'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='external')

    # Fix reverse accessor clashes by setting related_name
    groups = models.ManyToManyField(
        Group,
        related_name='authentication_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='authentication_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"