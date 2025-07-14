<<<<<<< Updated upstream
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
=======
from django.contrib.auth.models import AbstractUser, Group, Permission
>>>>>>> Stashed changes
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from .managers import UserManager
from django.utils.translation import gettext_lazy as _

<<<<<<< Updated upstream
class User(AbstractBaseUser, PermissionsMixin):

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
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    role = models.CharField(max_length=15 ,choices=ROLE_CHOICES, default='external', db_index=True)
   

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh':str(refresh),
            'access':str(refresh.access_token)
        }


class OneTimePassword(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)

    def __srt__(self):
        return f'{self.user.first_name}-passcode'
=======
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
>>>>>>> Stashed changes
