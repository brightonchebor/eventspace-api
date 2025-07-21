from django.urls import path
from .views import ListSpacesView

urlpatterns = [
    path('', ListSpacesView.as_view(), name='list-spaces'),
]