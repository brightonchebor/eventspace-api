from celery import shared_task
from django.utils import timezone
from django.db import models as django_models
from .models import Event
from apps.spaces.models import Space

@shared_task
def update_space_status():
    """
    Check for events that have ended and update their space status to 'free'
    """
    now = timezone.now()
    today = now.date()
    
    # Find all confirmed events that have ended
    # For standard time frame bookings
    ended_events_datetime = Event.objects.filter(
        is_full_day=False,
        end_datetime__lt=now,
        status='confirmed'
    ).select_related('space')
    
    # For multi-day bookings
    ended_events_date = Event.objects.filter(
        is_full_day=True,
        end_date__lt=today,
        status='confirmed'
    ).select_related('space')
    
    # Combine the querysets
    ended_events = list(ended_events_datetime) + list(ended_events_date)
    
    # Update space status for each event
    updated_spaces = 0
    completed_events = 0
    
    for event in ended_events:
        # Check if there are any upcoming events for this space
        now = timezone.now()
        today = now.date()
        
        # Check for both types of bookings
        has_upcoming_events = Event.objects.filter(
            django_models.Q(
                # Standard time frame bookings
                django_models.Q(
                    is_full_day=False,
                    end_datetime__gt=now,
                    status='confirmed'
                ) |
                # Multi-day bookings
                django_models.Q(
                    is_full_day=True,
                    end_date__gt=today,
                    status='confirmed'
                )
            ),
            space=event.space
        ).exclude(id=event.id).exists()
        
        if not has_upcoming_events:
            # If no upcoming events, mark space as free
            space = event.space
            if space.status != 'free':
                space.status = 'free'
                space.save(update_fields=['status'])
                updated_spaces += 1
        
        # Update event status to 'completed'
        event.status = 'completed'
        event.save(update_fields=['status'])
        completed_events += 1
    
    return f"Completed {completed_events} events and freed {updated_spaces} spaces"

@shared_task
def check_pending_events():
    """
    Check for pending events that need attention
    """
    now = timezone.now()
    tomorrow = now + timezone.timedelta(hours=24)
    tomorrow_date = tomorrow.date()
    
    # Find pending events that are starting soon (within 24 hours)
    # Standard time frame bookings
    soon_events_datetime = Event.objects.filter(
        is_full_day=False,
        start_datetime__lt=tomorrow,
        status='pending'
    )
    
    # Multi-day bookings
    soon_events_date = Event.objects.filter(
        is_full_day=True,
        start_date__lte=tomorrow_date,
        status='pending'
    )
    
    total_count = soon_events_datetime.count() + soon_events_date.count()
    return f"Found {total_count} pending events that are starting within 24 hours"

@shared_task
def update_space_on_approval(event_id):
    """
    Update space status when an event is approved
    """
    try:
        event = Event.objects.get(id=event_id)
        if event.status == 'confirmed':
            space = event.space
            space.status = 'booked'
            space.save(update_fields=['status'])
            return f"Space '{space.name}' marked as booked for event '{event.event_name}'"
    except Event.DoesNotExist:
        return f"Event with ID {event_id} not found"
