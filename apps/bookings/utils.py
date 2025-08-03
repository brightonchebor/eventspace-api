from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.image import MIMEImage
import os

def send_booking_rejected_email(event):
    """
    Send rejection notification email to user
    """
    if not event.user or not event.user.email:
        return False
    
    # Context for email template
    context = {
        'first_name': event.user.first_name or 'User',
        'event': event,
        'spaces': event.space.name if event.space else '',
    }
    
    # Render HTML message
    html_message = render_to_string('emails/booking_rejected.html', context)
    text_message = f"We regret to inform you that your booking for event '{event.event_name}' has not been approved at this time."
    
    # Create email message
    subject = f"Booking Not Approved: {event.event_name}"
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[event.user.email]
    )
    email.attach_alternative(html_message, "text/html")
    
    # Send email
    return email.send(fail_silently=True)
