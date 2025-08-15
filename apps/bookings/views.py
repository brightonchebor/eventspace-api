from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
import uuid

from .models import Event, Booking
from .serializers import EventSerializer, EventListSerializer, BookingSerializer
from .tasks import update_space_on_approval
from apps.spaces.models import Space

class BookEventView(CreateAPIView):
    """
    Book a new event
    """
    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Book a new event',
        operation_description='Create a new event booking and automatically update space status. Can book either for specific time frames (using start_datetime and end_datetime) or for full days (using start_date, end_date and is_full_day=True)',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_name', 'organizer_name', 'organizer_email', 'event_type', 'space'],
            properties={
                'event_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the event'),
                'start_datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Start date and time for time-specific bookings (ISO format)'),
                'end_datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='End date and time for time-specific bookings (ISO format)'),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Start date for multi-day bookings'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='End date for multi-day bookings'),
                'is_full_day': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Set to true for full-day bookings (use with start_date and end_date)'),
                'organizer_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the event organizer'),
                'organizer_email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email of the event organizer'),
                'event_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['meeting', 'conference', 'webinar', 'workshop'], description='Type of event being booked'),
                'attendance': openapi.Schema(type=openapi.TYPE_INTEGER, description='Expected number of attendees (optional)', nullable=True),
                'space': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the space where the event will be held')
            }
        ),
        responses={
            201: openapi.Response(
                description='Event booked successfully',
                schema=EventSerializer
            ),
            400: openapi.Response(
                description='Bad request - validation errors'
            ),
            404: openapi.Response(
                description='Space not found'
            ),
            409: openapi.Response(
                description='Conflict - space already booked for this time'
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                space = serializer.validated_data['space']
                is_full_day = serializer.validated_data.get('is_full_day', False)
                
                # Check if space is available
                if space.status != 'free':
                    return Response({
                        'message': 'Space is not available for booking',
                        'error': f'Space "{space.name}" is currently {space.status}'
                    }, status=status.HTTP_409_CONFLICT)
                
                # Check for conflicting bookings based on booking type
                if is_full_day:
                    # Full-day booking
                    start_date = serializer.validated_data.get('start_date')
                    end_date = serializer.validated_data.get('end_date')
                    
                    if not start_date or not end_date:
                        return Response({
                            'message': 'For full-day bookings, both start_date and end_date are required'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check for conflicts with other full-day bookings
                    conflicting_full_day = Event.objects.filter(
                        space=space,
                        is_full_day=True,
                        status__in=['pending', 'confirmed'],
                        start_date__lte=end_date,
                        end_date__gte=start_date
                    )
                    
                    # Check for conflicts with time-specific bookings
                    from django.db.models import Q
                    date_overlap_condition = Q(start_datetime__date__lte=end_date) & Q(end_datetime__date__gte=start_date)
                    conflicting_time_specific = Event.objects.filter(
                        space=space,
                        is_full_day=False,
                        status__in=['pending', 'confirmed'],
                        # Any event on the same dates conflicts with full-day booking
                    ).filter(date_overlap_condition)
                    
                    conflicting_events = list(conflicting_full_day) + list(conflicting_time_specific)
                    
                else:
                    # Time-specific booking
                    start_time = serializer.validated_data['start_datetime']
                    end_time = serializer.validated_data['end_datetime']
                    
                    # Check for conflicts with other time-specific bookings
                    conflicting_time_specific = Event.objects.filter(
                        space=space,
                        is_full_day=False,
                        status__in=['pending', 'confirmed'],
                        start_datetime__lt=end_time,
                        end_datetime__gt=start_time
                    )
                    
                    # Check for conflicts with full-day bookings
                    start_date = start_time.date()
                    end_date = end_time.date()
                    
                    conflicting_full_day = Event.objects.filter(
                        space=space,
                        is_full_day=True,
                        status__in=['pending', 'confirmed'],
                        start_date__lte=end_date,
                        end_date__gte=start_date
                    )
                    
                    conflicting_events = list(conflicting_time_specific) + list(conflicting_full_day)
                
                if len(conflicting_events) > 0:
                    # Get the conflicting event details
                    conflict = conflicting_events[0]
                    conflict_details = {
                        'booked_event': conflict.event_name,
                        'status': conflict.status
                    }
                    
                    # Add appropriate time details based on the conflict type
                    if conflict.is_full_day:
                        conflict_details.update({
                            'booking_type': 'full-day',
                            'from': conflict.start_date.strftime('%Y-%m-%d'),
                            'to': conflict.end_date.strftime('%Y-%m-%d')
                        })
                    else:
                        conflict_details.update({
                            'booking_type': 'time-specific',
                            'from': conflict.start_datetime.strftime('%Y-%m-%d %H:%M'),
                            'to': conflict.end_datetime.strftime('%Y-%m-%d %H:%M')
                        })
                        
                    return Response({
                        'message': 'Space already booked for this time',
                        'details': conflict_details
                    }, status=status.HTTP_409_CONFLICT)
                
                # Create the event with pending status (requires admin approval)
                event = serializer.save(
                    user=request.user,
                    status='pending'  # Always start as pending
                )
                
                # Space remains 'free' until event is approved by admin
                # (No space status change here)

                # --- Email Notification Trigger ---
                subject = f'Event Booking Submitted: {event.event_name}'
                
                # Prepare timing information based on booking type
                if event.is_full_day:
                    timing_info = (
                        f'Start Date: {event.start_date.strftime("%B %d, %Y")}\n'
                        f'End Date: {event.end_date.strftime("%B %d, %Y")}\n'
                        f'Booking Type: Full Day\n'
                    )
                else:
                    timing_info = (
                        f'Date: {event.start_datetime.strftime("%B %d, %Y")}\n'
                        f'Time: {event.start_datetime.strftime("%I:%M %p")} - {event.end_datetime.strftime("%I:%M %p")}\n'
                    )
                
                # Plain text version (fallback)
                message = (
                    f'Your event "{event.event_name}" has been submitted and is pending approval.\n'
                    f'Space: {space.name}\n'
                    f'{timing_info}'
                    f'Status: pending\n'
                    f'You will be notified once an admin approves your event.\n'
                )
                
                # User email
                user_email = request.user.email
                user_name = request.user.get_full_name() if hasattr(request.user, 'get_full_name') and callable(request.user.get_full_name) else f"{request.user.first_name} {request.user.last_name}"
                
                # Organizer email (assuming space.organizer.email exists)
                organizer_email = getattr(space.organizer, 'email', None) if space.organizer else None
                
                # Admin email (from settings)
                admin_email = settings.ADMIN_EMAIL

                # Set datetime values based on booking type
                if event.is_full_day:
                    # Format dates for full-day bookings
                    start_display = event.start_date.strftime('%B %d, %Y')
                    end_display = event.end_date.strftime('%B %d, %Y')
                else:
                    # Format datetime for time-specific bookings
                    start_date = event.start_datetime.strftime('%B %d, %Y')
                    start_time = event.start_datetime.strftime('%I:%M %p')
                    end_time = event.end_datetime.strftime('%I:%M %p')
                    
                    start_display = f"{start_date} {start_time}"
                    end_display = f"{event.end_datetime.strftime('%B %d, %Y')} {end_time}"
                
                # HTML version for the user
                context = {
                    'subject': subject,
                    'user_name': user_name,
                    'event_name': event.event_name,
                    'space_name': space.name,
                    'start_datetime': start_display,
                    'end_datetime': end_display,
                    'is_full_day': event.is_full_day
                }
                html_message = render_to_string('emails/booking_submitted.html', context)
                
                # Send email to user with proper error logging
                try:
                    if user_email:
                        email_message = EmailMultiAlternatives(
                            subject=subject,
                            body=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[user_email]
                        )
                        email_message.attach_alternative(html_message, "text/html")
                        email_message.send(fail_silently=False)
                        print(f"User booking notification email sent to {user_email}")
                except Exception as e:
                    print(f"Failed to send user notification email: {str(e)}")
                
                # Send to others (organizer, admin)
                try:
                    other_recipients = [email for email in [organizer_email, admin_email] if email]
                    if other_recipients:
                        organizer_context = {
                            'subject': f"New Booking Request: {event.event_name}",
                            'event_name': event.event_name,
                            'space_name': space.name,
                            'start_datetime': start_display,
                            'end_datetime': end_display,
                            'is_full_day': event.is_full_day,
                            'user_name': user_name,
                            'user_email': user_email
                        }
                        
                        html_organizer_message = render_to_string('emails/booking_pending_organizer.html', organizer_context)
                        
                        for recipient in other_recipients:
                            email_message = EmailMultiAlternatives(
                                subject=f"New Booking Request: {event.event_name}",
                                body=message,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                to=[recipient]
                            )
                            email_message.attach_alternative(html_organizer_message, "text/html")
                            email_message.send(fail_silently=False)
                            print(f"Organizer/admin notification email sent to {recipient}")
                except Exception as e:
                    print(f"Failed to send organizer/admin notification email: {str(e)}")
                # Send booking receipt
                self.send_booking_receipt(event, request.user)
                
                # --- End Email Notification ---

                # Format response data based on booking type
                response_data = {
                    'message': 'Event booked successfully',
                    'event_name': event.event_name,
                    'space': space.name,
                    'status': event.status
                }
                
                # Add appropriate time details based on booking type
                if event.is_full_day:
                    response_data.update({
                        'booking_type': 'full-day',
                        'start_date': event.start_date.strftime('%Y-%m-%d'),
                        'end_date': event.end_date.strftime('%Y-%m-%d')
                    })
                else:
                    response_data.update({
                        'booking_type': 'time-specific',
                        'start_time': event.start_datetime.strftime('%Y-%m-%d %H:%M'),
                        'end_time': event.end_datetime.strftime('%Y-%m-%d %H:%M')
                    })

                return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'Failed to book event',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    def send_booking_receipt(self, event, user):
        """
        Send a pending booking receipt email to the user
        """
        import uuid
        from django.utils import timezone
        
        try:
            space = event.space
            user_email = user.email
            
            # Generate a pending transaction ID 
            transaction_id = f"PENDING-{uuid.uuid4().hex[:8].upper()}"
            
            # Set datetime values based on booking type
            if event.is_full_day:
                # Format dates for full-day bookings
                start_display = event.start_date.strftime('%B %d, %Y')
                end_display = event.end_date.strftime('%B %d, %Y')
            else:
                # Format datetime for time-specific bookings
                start_date = event.start_datetime.strftime('%B %d, %Y')
                start_time = event.start_datetime.strftime('%I:%M %p')
                end_time = event.end_datetime.strftime('%I:%M %p')
                
                start_display = f"{start_date} {start_time}"
                end_display = f"{event.end_datetime.strftime('%B %d, %Y')} {end_time}"
            
            # Calculate estimated price (will be finalized upon approval)
            if event.is_full_day:
                # For full day booking, use price_per_day
                delta = (event.end_date - event.start_date).days + 1
                price = space.price_per_day * delta if space.price_per_day else 0
                amount_paid = f"Ksh. {price} (Est. - {delta} days at Ksh. {space.price_per_day}/day)" if space.price_per_day else "Free"
            else:
                # For time-specific booking (not hourly)
                duration = (event.end_datetime - event.start_datetime).total_seconds() / 3600
                days = int(duration / 24)
                remaining_hours = duration % 24
                
                if days > 0:
                    price = space.price_per_day * days if space.price_per_day else 0
                    amount_paid = f"Ksh. {price} (Est. - {days} days at Ksh. {space.price_per_day}/day)"
                else:
                    price = space.price_per_day if space.price_per_day else 0
                    amount_paid = f"Ksh. {price} (Est. - daily rate)"
            
            subject = f'Booking Receipt (Pending) - {event.event_name}'
            
            # Plain text version
            message = (
                f'PENDING BOOKING RECEIPT\n\n'
                f'Event: {event.event_name}\n'
                f'Space: {space.name}\n'
                f'Location: {space.location}\n'
                f'Booking Date: {start_display} to {end_display}\n\n'
                f'Estimated Amount: {amount_paid}\n'
                f'Booking Date: {timezone.now().strftime("%B %d, %Y %I:%M %p")}\n'
                f'Reference ID: {transaction_id}\n'
                f'Status: PENDING APPROVAL\n\n'
                f'Your booking is awaiting approval. You will receive a final receipt once approved.\n'
                f'Thank you for your booking!\n'
            )
            
            # HTML version
            context = {
                'event_name': event.event_name,
                'space_name': space.name,
                'space_location': space.location,
                'start_datetime': start_display,
                'end_datetime': end_display,
                'is_full_day': event.is_full_day,
                'organizer_name': event.organizer_name,
                'amount_paid': amount_paid,
                'payment_date': timezone.now().strftime("%B %d, %Y %I:%M %p"),
                'transaction_id': transaction_id,
                'payment_method': 'Pending',
                'status': 'PENDING APPROVAL'
            }
            
            html_message = render_to_string('emails/booking_receipt.html', context)
            
            # Send email
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send(fail_silently=False)
            print(f"Pending booking receipt email sent to {user_email}")
            
        except Exception as e:
            print(f"Failed to send booking receipt: {str(e)}")

class ListUpcomingEventsView(ListAPIView):
    """
    List all upcoming events
    """
    serializer_class = EventListSerializer

    def get_queryset(self):
        """Get all upcoming events (confirmed and in the future)"""
        now = timezone.now()
        return Event.objects.filter(
            status='confirmed',
            start_datetime__gt=now
        ).select_related('space', 'user').order_by('start_datetime')

    @swagger_auto_schema(
        operation_summary='List upcoming confirmed events',
        operation_description='Get a list of all upcoming confirmed events ordered by start date (nearest first)',
        manual_parameters=[
            openapi.Parameter(
                'event_type',
                openapi.IN_QUERY,
                description='Filter events by type',
                type=openapi.TYPE_STRING,
                enum=['meeting', 'conference', 'webinar', 'workshop']
            ),
        ],
        responses={
            200: openapi.Response(
                description='List of upcoming confirmed events retrieved successfully',
                schema=EventListSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Optional filtering by event type
        event_type_filter = request.query_params.get('event_type', None)
        if event_type_filter:
            queryset = queryset.filter(event_type=event_type_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'message': f'Found {queryset.count()} upcoming events',
            'count': queryset.count(),
            'data': serializer.data
        })

class ListMyEventsView(ListAPIView):
    """
    List events for the authenticated user
    """
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter events to show all events created by the current user regardless of status
        """
        return Event.objects.filter(
            user=self.request.user  # Current user's events - no status filter
        ).select_related('space').order_by('start_datetime')

    @swagger_auto_schema(
        operation_summary='List all my events',
        operation_description='Get a list of all events created by the current user regardless of status',
        responses={
            200: openapi.Response(
                description='User events retrieved successfully',
                schema=EventListSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Group events by status
        events_by_status = {}
        for event in queryset:
            status_key = event.status
            if status_key not in events_by_status:
                events_by_status[status_key] = 0
            events_by_status[status_key] += 1
        
        return Response({
            'message': f'Found {queryset.count()} events for user {request.user.email}',
            'count': queryset.count(),
            'events_by_status': events_by_status,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
class ApproveEventView(APIView):
    """
    Approve a pending event
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary='Approve an event',
        operation_description='Change the status of a pending event to confirmed',
        manual_parameters=[
            openapi.Parameter(
                'event_id',
                openapi.IN_PATH,
                description='ID of the event to approve',
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description='Event approved successfully'
            ),
            400: openapi.Response(
                description='Bad request - event already approved or cancelled'
            ),
            404: openapi.Response(
                description='Event not found'
            )
        }
    )
    def post(self, request, event_id):
        try:
            # Print template debug info
            from django.conf import settings
            print(f"TEMPLATE_DEBUG: {settings.TEMPLATES[0]['OPTIONS'].get('debug', False)}")
            print(f"TEMPLATE_DIRS: {settings.TEMPLATES[0]['DIRS']}")
            import os
            print(f"Templates exist check:")
            for dir_path in settings.TEMPLATES[0]['DIRS']:
                template_path = os.path.join(dir_path, 'emails', 'booking_approved.html')
                print(f"  - {template_path} exists: {os.path.isfile(template_path)}")
            
            event = Event.objects.get(id=event_id)
            
            if event.status != 'pending':
                return Response({
                    'message': f'Event cannot be approved. Current status: {event.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update event status
            event.status = 'confirmed'
            event.save()
            
            # Trigger Celery task to update space status
            update_space_on_approval.delay(event.id)
            
            # Send booking approval email with better error handling
            try:
                self.send_approval_notification(event)
                print(f"Successfully sent approval notification for event ID: {event.id}")
            except Exception as e:
                print(f"Error sending approval notification: {str(e)}")
            
            # Send payment receipt email with separate error handling
            try:
                self.send_payment_receipt(event)
                print(f"Successfully sent payment receipt for event ID: {event.id}")
            except Exception as e:
                print(f"Error sending payment receipt: {str(e)}")
            
            return Response({
                'message': f'Event "{event.event_name}" has been approved successfully',
                'event_id': event.id,
                'space': event.space.name,
                'note': 'Space status will be updated shortly'
            }, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({
                'message': 'Event not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    def send_approval_notification(self, event):
        """
        Send a booking approval notification to the user
        """
        try:
            from django.utils import timezone
            
            space = event.space
            user = event.user
            user_email = user.email
            user_name = user.get_full_name() if hasattr(user, 'get_full_name') and callable(user.get_full_name) else f"{user.first_name} {user.last_name}"
            
            # Set datetime values based on booking type
            if event.is_full_day:
                start_display = event.start_date.strftime('%B %d, %Y')
                end_display = event.end_date.strftime('%B %d, %Y')
            else:
                start_date = event.start_datetime.strftime('%B %d, %Y')
                start_time = event.start_datetime.strftime('%I:%M %p')
                end_time = event.end_datetime.strftime('%I:%M %p')
                
                start_display = f"{start_date} {start_time}"
                end_display = f"{event.end_datetime.strftime('%B %d, %Y')} {end_time}"
            
            subject = f'Booking Approved - {event.event_name}'
            
            # Plain text version
            message = (
                f"Dear {user_name},\n\n"
                f"Great news! Your booking for event '{event.event_name}' has been approved.\n\n"
                f"Event Details:\n"
                f"- Event: {event.event_name}\n"
                f"- Space: {space.name}\n"
                f"- Location: {space.location}\n"
                f"- Date/Time: {start_display} to {end_display}\n"
                f"- Status: Approved\n\n"
                f"We're looking forward to hosting your event. Your payment receipt has been sent in a separate email.\n\n"
                f"If you have any questions or need assistance, please don't hesitate to contact us.\n\n"
                f"Regards,\n"
                f"EventSpace Team"
            )
            
            # HTML version with proper context
            context = {
                'user_name': user_name,
                'event_name': event.event_name,
                'space_name': space.name,
                'space_location': space.location,
                'start_datetime': start_display,
                'end_datetime': end_display,
                'is_full_day': event.is_full_day,
                'status': 'Approved'
            }
            
            html_message = render_to_string('emails/booking_approved.html', context)
            
            # Print extensive debug information before sending
            print(f"Preparing to send approval email to {user_email}")
            print(f"Event name: {event.event_name}")
            print(f"Space name: {space.name}")
            print(f"Context keys: {context.keys()}")
            print(f"Context values for debugging:")
            for key, value in context.items():
                print(f"  - {key}: {value}")
            print(f"Template path: emails/booking_approved.html")
            
            # Ensure user_name is in context (explicitly double check)
            if 'user_name' not in context or not context['user_name']:
                print("WARNING: user_name missing or empty in context, adding it explicitly")
                context['user_name'] = user_name
            
            # Try with a simple inline template first to test rendering
            simple_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Booking Approved</title></head>
            <body>
                <h1>Booking Approved for {event.event_name}</h1>
                <p>Dear {user_name},</p>
                <p>Your booking has been approved for {space.name}.</p>
                <p>From {start_display} to {end_display}</p>
            </body>
            </html>
            """
            
            # Now try with the actual template
            html_message = render_to_string('emails/booking_approved.html', context)
            print(f"HTML message length: {len(html_message)}")
            print(f"HTML message preview: {html_message[:100]}...")
            
            # Compare with simple template length
            print(f"Simple HTML length: {len(simple_html)}")
            
            # Use the simple template if the rendered one is empty
            if len(html_message.strip()) < 10:
                print("WARNING: Rendered HTML is too short, using simple template instead")
                html_message = simple_html
            
            # Send email
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email_message.attach_alternative(html_message, "text/html")
            result = email_message.send(fail_silently=False)
            print(f"Booking approval notification email sent to {user_email}, result: {result}")
            
        except Exception as e:
            print(f"Failed to send approval notification: {str(e)}")
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
            
    def send_payment_receipt(self, event):
        """
        Send a payment receipt email when an event is approved
        """
        from django.utils import timezone
        import uuid
        
        try:
            space = event.space
            user_email = event.user.email
            user_name = event.user.get_full_name() if hasattr(event.user, 'get_full_name') and callable(event.user.get_full_name) else f"{event.user.first_name} {event.user.last_name}"
            
            # Print debug information
            print(f"Preparing to send payment receipt to {user_email}")
            print(f"Event ID: {event.id}")
            print(f"Event name: {event.event_name}")
            print(f"Space name: {space.name}")
            print(f"Space price_per_day: {space.price_per_day}")
            
            # Get organizer and admin emails
            organizer_email = getattr(space.organizer, 'email', None) if space.organizer else None
            admin_email = settings.ADMIN_EMAIL
            
            # Calculate price based on booking type
            if event.is_full_day:
                # For full day booking, use price_per_day
                # Calculate number of days
                delta = (event.end_date - event.start_date).days + 1  # Include both start and end date
                price = space.price_per_day * delta if space.price_per_day else 0
                amount_paid = f"Ksh. {price} ({delta} days at Ksh. {space.price_per_day}/day)" if space.price_per_day else "Free"
            else:
                # For time-specific booking (not hourly), use daily rate
                duration = (event.end_datetime - event.start_datetime).total_seconds() / 3600  # hours
                days = int(duration / 24)
                remaining_hours = duration % 24
                
                if days > 0:
                    # For multi-day bookings
                    price = space.price_per_day * days if space.price_per_day else 0
                    amount_paid = f"Ksh. {price} ({days} days at Ksh. {space.price_per_day}/day)"
                else:
                    # For same-day bookings (less than 24 hours)
                    price = space.price_per_day if space.price_per_day else 0
                    amount_paid = f"Ksh. {price} (daily rate)"
            
            # Generate transaction ID
            transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            
            # Set datetime values based on booking type
            if event.is_full_day:
                # Format dates for full-day bookings
                start_display = event.start_date.strftime('%B %d, %Y')
                end_display = event.end_date.strftime('%B %d, %Y')
            else:
                # Format datetime for time-specific bookings
                start_date = event.start_datetime.strftime('%B %d, %Y')
                start_time = event.start_datetime.strftime('%I:%M %p')
                end_time = event.end_datetime.strftime('%I:%M %p')
                
                start_display = f"{start_date} {start_time}"
                end_display = f"{event.end_datetime.strftime('%B %d, %Y')} {end_time}"
            
            subject = f'Receipt for {event.event_name} - Booking Confirmed'
            
            # Plain text version (fallback)
            message = (
                f'RECEIPT\n\n'
                f'Event: {event.event_name}\n'
                f'Space: {space.name}\n'
                f'Location: {space.location}\n'
                f'Booking Date: {start_display} to {end_display}\n\n'
                f'Amount Paid: {amount_paid}\n'
                f'Payment Date: {timezone.now().strftime("%B %d, %Y %I:%M %p")}\n'
                f'Transaction ID: {transaction_id}\n'
                f'Payment Method: Credit Card\n'
                f'Status: CONFIRMED\n\n'
                f'Thank you for your booking!\n'
            )
            
            # HTML version
            context = {
                'event_name': event.event_name,
                'space_name': space.name,
                'space_location': space.location,
                'start_datetime': start_display,
                'end_datetime': end_display,
                'is_full_day': event.is_full_day,
                'organizer_name': event.organizer_name,
                'amount_paid': amount_paid,
                'payment_date': timezone.now().strftime("%B %d, %Y %I:%M %p"),
                'transaction_id': transaction_id,
                'payment_method': 'Credit Card',
                'status': 'CONFIRMED'
            }
            
            html_message = render_to_string('emails/booking_receipt.html', context)
            
            # Print extensive debug information before sending
            print(f"Payment receipt context keys: {context.keys()}")
            print(f"Payment receipt context values for debugging:")
            for key, value in context.items():
                print(f"  - {key}: {value}")
            print(f"Template path: emails/booking_receipt.html")
            
            # Try with a simple inline template first to test rendering
            simple_receipt_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Payment Receipt</title></head>
            <body>
                <h1>Payment Receipt for {event.event_name}</h1>
                <p>Event: {event.event_name}</p>
                <p>Space: {space.name}</p>
                <p>From: {start_display} to {end_display}</p>
                <p>Amount: {amount_paid}</p>
                <p>Transaction ID: {transaction_id}</p>
                <p>Status: {context['status']}</p>
            </body>
            </html>
            """
            
            # Now try with the actual template
            html_message = render_to_string('emails/booking_receipt.html', context)
            print(f"Receipt HTML message length: {len(html_message)}")
            print(f"Receipt HTML message preview: {html_message[:100]}...")
            
            # Compare with simple template length
            print(f"Simple receipt HTML length: {len(simple_receipt_html)}")
            
            # Use the simple template if the rendered one is empty
            if len(html_message.strip()) < 10:
                print("WARNING: Rendered receipt HTML is too short, using simple template instead")
                html_message = simple_receipt_html
            
            # Send email to user with better error handling
            try:
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user_email]
                )
                email_message.attach_alternative(html_message, "text/html")
                result = email_message.send(fail_silently=False)
                print(f"Booking receipt email sent to {user_email}, result: {result}")
            except Exception as e:
                print(f"Failed to send user booking receipt: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Send notification to organizer if available
            if organizer_email:
                try:
                    organizer_context = context.copy()
                    organizer_context['recipient_type'] = 'organizer'
                    
                    organizer_subject = f'Space Booking Confirmed: {event.event_name}'
                    organizer_html = render_to_string('emails/booking_approved.html', organizer_context)
                    
                    org_email = EmailMultiAlternatives(
                        subject=organizer_subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[organizer_email]
                    )
                    org_email.attach_alternative(organizer_html, "text/html")
                    org_email.send(fail_silently=False)
                    print(f"Organizer notification email sent to {organizer_email}")
                except Exception as e:
                    print(f"Failed to send organizer notification: {str(e)}")
                
            # Send notification copy to admin
            if admin_email:
                try:
                    admin_subject = f'Admin Copy: Booking Confirmed - {event.event_name}'
                    
                    admin_email_msg = EmailMultiAlternatives(
                        subject=admin_subject,
                        body=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[admin_email]
                    )
                    admin_email_msg.attach_alternative(html_message, "text/html")
                    admin_email_msg.send(fail_silently=False)
                    print(f"Admin notification email sent to {admin_email}")
                except Exception as e:
                    print(f"Failed to send admin notification: {str(e)}")
                
        except Exception as e:
            print(f"Failed to send payment receipt: {str(e)}")
            import traceback
            traceback.print_exc()


class CheckEventStatusView(APIView):
    """
    Check and update status of events that have ended
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary='Check event status',
        operation_description='Mark completed events and update space status',
        responses={
            200: openapi.Response(
                description='Events checked and updated'
            )
        }
    )
    def post(self, request):
        # Find all confirmed events that have ended
        ended_events = Event.objects.filter(
            status='confirmed',
            end_datetime__lt=timezone.now()
        )
        
        count = 0
        for event in ended_events:
            event.status = 'completed'
            event.save()  # This will trigger the signal to update space status
            count += 1
        
        return Response({
            'message': f'Checked event status. Marked {count} events as completed.',
        }, status=status.HTTP_200_OK)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create a new booking",
        operation_description="Create a new booking for an event space",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_name', 'start_datetime', 'end_datetime', 'organizer_name', 
                     'organizer_email', 'event_type', 'attendance', 'space'],
            properties={
                'event_name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the event"),
                'start_datetime': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Start date and time of the booking"),
                'end_datetime': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="End date and time of the booking"),
                'organizer_name': openapi.Schema(type=openapi.TYPE_STRING, description="Name of the event organizer"),
                'organizer_email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Email of the event organizer"),
                'event_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type of event (e.g., Internal, Workshop, Conference)"),
                'attendance': openapi.Schema(type=openapi.TYPE_INTEGER, description="Expected number of attendees"),
                'required_resources': openapi.Schema(type=openapi.TYPE_STRING, description="Resources needed (e.g., Projector, Whiteboard, Video Conferencing)"),
                'space': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the space being booked"),
            }
        ),
        responses={
            201: openapi.Response(description="Booking created successfully", schema=BookingSerializer),
            400: "Bad Request - Invalid data",
            403: "Permission Denied"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set the current user as the booking user
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)