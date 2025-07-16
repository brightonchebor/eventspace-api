from django.urls import path
from .views import BookEventView, ListUpcomingEventsView, ListMyEventsView

urlpatterns = [
    path('book/', BookEventView.as_view(), name='book-event'),
    path('upcoming/', ListUpcomingEventsView.as_view(), name='upcoming-events'),
    path('my-events/', ListMyEventsView.as_view(), name='my-events'),
]