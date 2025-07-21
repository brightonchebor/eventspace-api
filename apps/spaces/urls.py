from django.urls import path
from .views import CreateSpaceView

urlpatterns = [
    path('', ListSpacesView.as_view(), name='list-spaces'),
]