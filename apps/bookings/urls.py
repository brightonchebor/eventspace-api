from django.urls import path
from .views import (
    BookEventView, 
    ListUpcomingEventsView, 
    ListMyEventsView, 
    ApproveEventView,
    CheckEventStatusView
)

urlpatterns = [
    path('book/', BookEventView.as_view(), name='book-event'),
    path('upcoming/', ListUpcomingEventsView.as_view(), name='upcoming-events'),
    path('my-events/', ListMyEventsView.as_view(), name='my-events'),
    path('approve/<int:event_id>/', ApproveEventView.as_view(), name='approve-event'),
    path('check-status/', CheckEventStatusView.as_view(), name='check-event-status'),
]