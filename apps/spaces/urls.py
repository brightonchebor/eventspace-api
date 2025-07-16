from django.urls import path
from .views import CreateSpaceView, ListSpacesView

urlpatterns = [
    path('', ListSpacesView.as_view(), name='list-spaces'),
    path('create/', CreateSpaceView.as_view(), name='create-space'),
]