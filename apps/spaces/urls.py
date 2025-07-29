from django.urls import path
from .views import list_spaces, space_detail,delete_space

urlpatterns = [
    path('', list_spaces, name='list-spaces'),
    path('<int:pk>/', space_detail, name='space-detail'),
    path('<int:pk>/delete/', delete_space, name='delete-space'),
]