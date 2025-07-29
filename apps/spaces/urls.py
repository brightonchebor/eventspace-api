from django.urls import path
from .views import list_spaces, space_detail

urlpatterns = [
    path('', list_spaces, name='list-spaces'),
    path('<int:pk>/', space_detail, name='space-detail'),
]