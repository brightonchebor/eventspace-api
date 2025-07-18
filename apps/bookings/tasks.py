from celery import shared_task
from django.utils import timezone
from .models import Event
from apps.spaces.models import Space

@shared_task
def update_space_status():
    """
    Check for events that have ended and update their space status to 'free'
    """
    # Find all confirmed events that have ended
    ended_events = Event.objects.filter(
        end_datetime__lt=timezone.now(),
        status='confirmed'
    ).select_related('space')
    
    # Update space status for each event
    updated_spaces = 0
    completed_events = 0
    
    for event in ended_events:
        # Check if there are any upcoming events for this space
        has_upcoming_events = Event.objects.filter(
            space=event.space,
            end_datetime__gt=timezone.now(),
            status='confirmed'
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
    # Find pending events that are starting soon (within 24 hours)
    soon_events = Event.objects.filter(
        start_datetime__lt=timezone.now() + timezone.timedelta(hours=24),
        status='pending'
    )
    
    return f"Found {soon_events.count()} pending events that are starting within 24 hours"

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
