from django.urls import path
from .views import list_spaces, space_detail, CreateSpaceView

urlpatterns = [
    path('', list_spaces, name='list-spaces'),
    path('<int:pk>/', space_detail, name='space-detail'),
    path('create/', CreateSpaceView.as_view(), name='create-space'),
]