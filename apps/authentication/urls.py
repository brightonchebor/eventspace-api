from django.urls import path
<<<<<<< HEAD
from .views import UserRegisterView
from .views import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
   path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
=======
from .views import UserRegisterView, VerifyUserEmail,LoginUserView


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
     path('verify-email/', VerifyUserEmail.as_view(), name='verify'),
     path('login/',LoginUserView.as_view(), name="login")

>>>>>>> d248cbbeb8dac013d9e3d0627ebfcf2cfc20128e
]
