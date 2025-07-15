from django.urls import path
from .views import UserRegisterView, VerifyUserEmail


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
     path('verify-email/', VerifyUserEmail.as_view(), name='verify'),

]
