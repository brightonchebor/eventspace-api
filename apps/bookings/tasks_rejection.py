from celery import shared_task

@shared_task
def reject_booking(event_id):
    """
    Handle booking rejection process and send notification
    """
    from .models import Event
    from .utils import send_booking_rejected_email
    
    try:
        event = Event.objects.select_related('user').get(id=event_id)
        # Update status to rejected
        event.status = 'rejected'
        event.save(update_fields=['status'])
        
        # Send rejection email
        send_booking_rejected_email(event)
        
        return f"Booking for '{event.event_name}' has been rejected and user notified"
    except Event.DoesNotExist:
        return f"Event with ID {event_id} not found"
