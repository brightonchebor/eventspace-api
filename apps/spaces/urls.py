from django.urls import path
from .views import CreateSpaceView, ListSpacesView

urlpatterns = [
    path('create/', CreateSpaceView.as_view(), name='create-space'),
    path('', ListSpacesView.as_view(), name='list-spaces'),
]