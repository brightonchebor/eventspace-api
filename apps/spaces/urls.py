from django.urls import path
from .views import CreateSpaceView

urlpatterns = [
    path('create/', CreateSpaceView.as_view(), name='create-space'),
]