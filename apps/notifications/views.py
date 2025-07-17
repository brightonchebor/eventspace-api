from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json

from apps.bookings.models import Booking  # Booking model
from apps.authentication.models import User        # User model

def send_booking_notifications(event, spaces, user):
    # Organizer email
    organizer_email = event.organizer.email
    organizer_name = event.organizer.get_full_name() if hasattr(event.organizer, 'get_full_name') else event.organizer.username

    # Admin email (assuming settings.ADMINS is set)
    admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]

    # User email
    user_email = user.email
    user_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username

    subject = f"Booking Confirmation for Event: {event.name}"
    message = (
        f"Dear {organizer_name},\n\n"
        f"The event '{event.name}' has been booked by {user_name}.\n"
        f"Spaces booked: {spaces}\n\n"
        "Regards,\nEventSpace Team"
    )

    # Send to organizer
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [organizer_email])

    # Send to admin(s)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, admin_emails)

    # Send to user
    user_message = (
        f"Dear {user_name},\n\n"
        f"Your booking for event '{event.event_name}' and spaces {spaces} is confirmed.\n\n"
        "Regards,\nEventSpace Team"
    )
    send_mail(subject, user_message, settings.DEFAULT_FROM_EMAIL, [user_email])

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
        booking = Booking.objects.select_related('user', 'event').get(id=booking_id)
    except Booking.DoesNotExist:
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
