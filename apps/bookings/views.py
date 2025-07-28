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
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes

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
        operation_description='Create a new event booking and automatically update space status',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['event_name', 'start_datetime', 'end_datetime', 'organizer_name', 'organizer_email', 'event_type', 'space'],
            properties={
                'event_name': openapi.Schema(type=openapi.TYPE_STRING, description='Name of the event'),
                'start_datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Start date and time of the event (ISO format)'),
                'end_datetime': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='End date and time of the event (ISO format)'),
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
                start_time = serializer.validated_data['start_datetime']
                end_time = serializer.validated_data['end_datetime']
                
                # Check if space is available
                if space.status != 'free':
                    return Response({
                        'message': 'Space is not available for booking',
                        'error': f'Space "{space.name}" is currently {space.status}'
                    }, status=status.HTTP_409_CONFLICT)
                
                # Check for any conflicting bookings (both pending and confirmed events)
                conflicting_events = Event.objects.filter(
                    space=space,
                    status__in=['pending', 'confirmed'],  # Check both pending and confirmed events
                    start_datetime__lt=end_time,
                    end_datetime__gt=start_time
                )
                
                if conflicting_events.exists():
                    # Get the conflicting event details
                    conflict = conflicting_events.first()
                    return Response({
                        'message': 'Space already booked for this time',
                        'details': {
                            'booked_event': conflict.event_name,
                            'from': conflict.start_datetime.strftime('%Y-%m-%d %H:%M'),
                            'to': conflict.end_datetime.strftime('%Y-%m-%d %H:%M'),
                            'status': conflict.status
                        }
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
                message = (
                    f'Your event "{event.event_name}" has been submitted and is pending approval.\n'
                    f'Space: {space.name}\n'
                    f'Start: {start_time}\n'
                    f'End: {end_time}\n'
                    f'Status: pending\n'
                    f'You will be notified once an admin approves your event.\n'
                )
                # User email
                user_email = request.user.email
                # Organizer email (assuming space.organizer.email exists)
                organizer_email = getattr(space.organizer, 'email', None)
                # Admin email (from settings)
                admin_email = getattr(settings, 'ADMIN_EMAIL', None)

                recipient_list = [email for email in [user_email, organizer_email, admin_email] if email]

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=True
                )
                # --- End Email Notification ---

                return Response({
                    'message': 'Event booked successfully',
                    'event_name': event.event_name,
                    'space': space.name,
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M'),
                    'status': event.status
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'Failed to book event',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

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