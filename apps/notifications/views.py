from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import json

from apps.bookings.models import Event # Booking model
from apps.authentication.models import User # User model

def send_booking_notifications(event, spaces, user):
    # Organizer email
    organizer_email = event.organizer.email
    organizer_name = event.organizer.get_full_name() if hasattr(event.organizer, 'get_full_name') else event.organizer.username

    # Admin email (assuming settings.ADMINS is set)
    admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]

    # User email
    user_email = user.email
    user_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username

    # Email to organizer: booking pending approval
    subject_org = f"Booking Pending Approval: {event.event_name}"
    
    # Plain text version (fallback)
    message_org_plain = (
        f"Dear {organizer_name},\n\n"
        f"A new booking for event '{event.event_name}' has been made by {user_name}.\n"
        f"Spaces booked: {spaces}\n"
        "Status: Pending approval from admin.\n\n"
        "Regards,\nSmartSpace Team"
    )
    
    # HTML version
    context_org = {
        'subject': subject_org,
        'organizer_name': organizer_name,
        'user_name': user_name,
        'event': event,
        'spaces': spaces,
    }
    html_message_org = render_to_string('emails/booking_pending_organizer.html', context_org)
    
    # Send email to organizer
    email_org = EmailMultiAlternatives(
        subject_org,
        message_org_plain,
        settings.DEFAULT_FROM_EMAIL,
        [organizer_email]
    )
    email_org.attach_alternative(html_message_org, "text/html")
    email_org.send()

    # Email to admin(s): booking approval needed
    subject_admin = f"Booking Approval Needed: {event.event_name}"
    
    # Plain text version (fallback)
    message_admin_plain = (
        f"Admin,\n\n"
        f"A new booking for event '{event.event_name}' by {user_name} is awaiting your approval.\n"
        f"Spaces booked: {spaces}\n\n"
        "Regards,\nSmartSpace Team"
    )
    
    # HTML version
    context_admin = {
        'subject': subject_admin,
        'user_name': user_name,
        'organizer_name': organizer_name,
        'event': event,
        'spaces': spaces,
    }
    html_message_admin = render_to_string('emails/booking_pending_admin.html', context_admin)
    
    # Send email to admin(s)
    if admin_emails:
        email_admin = EmailMultiAlternatives(
            subject_admin,
            message_admin_plain,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails
        )
        email_admin.attach_alternative(html_message_admin, "text/html")
        email_admin.send()

@csrf_exempt
def notify_booking_created(request):
    """
    Send a notification to a user when they book an event.
    Expects POST data: {'booking_id': int}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        booking_id = data['booking_id']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data.'}, status=400)

    try:
        booking = Event.objects.select_related('user', 'event').get(id=booking_id)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Booking not found.'}, status=404)

    user = booking.user
    event = booking.event

    send_booking_notifications(event, booking.spaces, user)

    return JsonResponse({'success': True, 'message': f"Hi {user.username}, your booking for event '{event.event_name}' has been received."})
    message = f"Hi {user.username}, your booking for event '{event.name}' has been received."

    Notification.objects.create(user=user, message=message)
    # Or trigger an email, push notification, etc.

    send_booking_notifications(event, booking.spaces, user)

    return JsonResponse({'success': True, 'message': message})

def send_booking_approved_notification(event, spaces, user):
    user_email = user.email
    user_name = user.get_full_name() if callable(getattr(user, 'get_full_name', None)) else getattr(user, 'username', user.email)
    first_name = user.first_name if hasattr(user, 'first_name') else user_name

    subject = f"Booking Approved: {event.event_name}"
    
    # Plain text version (fallback)
    message_plain = (
        f"Dear {first_name},\n\n"
        f"Your booking for event '{event.event_name}' and spaces {spaces} has been approved by the admin.\n"
        "You may proceed with your event.\n\n"
        "Regards,\nSmartSpace Team"
    )
    
    # Try to get the space image URL if available
    space_image_url = None
    if event.space and event.space.image1:
        # First try to construct a full URL
        if hasattr(settings, 'SITE_URL'):
            space_image_url = settings.SITE_URL + settings.MEDIA_URL + str(event.space.image1)
        else:
            # Fallback to relative URL
            space_image_url = settings.MEDIA_URL + str(event.space.image1)
    
    # HTML version
    context = {
        'subject': subject,
        'first_name': first_name,
        'event': event,
        'spaces': spaces,
        'space_image': space_image_url,
    }
    html_message = render_to_string('emails/booking_approved.html', context)
    
    # Send email
    email = EmailMultiAlternatives(
        subject,
        message_plain,
        settings.DEFAULT_FROM_EMAIL,
        [user_email]
    )
    email.attach_alternative(html_message, "text/html")
    email.send()

def send_booking_rejected_notification(event, spaces, user):
    user_email = user.email 
    user_name = user.get_full_name() if callable(getattr(user, 'get_full_name', None)) else getattr(user, 'username', user.email)
    first_name = user.first_name if hasattr(user, 'first_name') else user_name
    subject = f"Booking Not Approved: {event.event_name}"

    # Plain text version (fallback)
    message_plain = (
        f"Dear {first_name},\n\n"
        f"Your booking for event '{event.event_name}' and spaces {spaces} has not been approved.\n"
        "Please contact support for further assistance.\n\n"
        "Regards,\nSmartSpace Team"
    )
    
    # HTML version
    context = {
        'subject': subject,
        'first_name': first_name,
        'event': event,
        'spaces': spaces,
    }
    html_message = render_to_string('emails/booking_rejected.html', context)
    
    # Send email
    email = EmailMultiAlternatives(
        subject,
        message_plain,
        settings.DEFAULT_FROM_EMAIL,
        [user_email]
    )
    email.attach_alternative(html_message, "text/html")
    email.send()


