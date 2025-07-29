from django.urls import path
from .views import *


urlpatterns = [
    path('api/users/register/', UserRegisterView.as_view(), name='register'),
    path('api/users/verify-email/', VerifyUserEmail.as_view(), name='verify'),
    path('api/users/login/',LoginUserView.as_view(), name="login"),
    path('api/users/logout/', LogoutUserView.as_view(), name='logout'),

    path('api/users/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='password-reset-confirm'),
<<<<<<< HEAD
    path('set-new-password/', SetNewPassword.as_view(), name='set-new-password'),
    path('users/delete-all/', DeleteAllUsersView.as_view(), name='delete-all-users'),
=======
    path('api/users/set-new-password/', SetNewPassword.as_view(), name='set-new-password'),
>>>>>>> b822cde82d3ff79e35c8e001afe33db317df025e

]
