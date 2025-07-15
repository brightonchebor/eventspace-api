from django.urls import path
from .views import UserRegisterView
from .views import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
   path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
