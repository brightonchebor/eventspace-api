from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction

from .models import Event
from .serializers import EventSerializer, EventListSerializer
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
        request_body=EventSerializer,
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
                
                # Check for conflicting bookings
                conflicting_events = Event.objects.filter(
                    space=space,
                    status__in=['confirmed', 'upcoming'],
                    start_datetime__lt=end_time,
                    end_datetime__gt=start_time
                )
                
                if conflicting_events.exists():
                    return Response({
                        'message': 'Time slot conflict',
                        'error': 'The selected time slot conflicts with existing bookings',
                        'conflicting_events': [
                            f"{event.event_name} ({event.start_datetime} - {event.end_datetime})"
                            for event in conflicting_events
                        ]
                    }, status=status.HTTP_409_CONFLICT)
                
                # Check space capacity
                attendance = serializer.validated_data['attendance']
                if attendance > space.capacity:
                    return Response({
                        'message': 'Attendance exceeds space capacity',
                        'error': f'Space capacity is {space.capacity}, but you requested for {attendance} attendees'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create the event with confirmed/upcoming status
                event_status = 'upcoming' if start_time > timezone.now() else 'confirmed'
                event = serializer.save(
                    user=request.user,
                    status=event_status
                )
                
                # Update space status to booked
                space.status = 'booked'
                space.save()
                
                return Response({
                    'message': f'Event "{event.event_name}" has been booked successfully',
                    'data': serializer.data,
                    'space_status': 'booked',
                    'event_status': event_status
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
        # Get all events that are upcoming or confirmed and in the future
        now = timezone.now()
        return Event.objects.filter(
            status__in=['upcoming', 'confirmed'],
            start_datetime__gt=now
        ).select_related('space', 'user').order_by('start_datetime')

    @swagger_auto_schema(
        operation_summary='List upcoming events',
        operation_description='Get a list of all upcoming events that are confirmed and scheduled for the future',
        responses={
            200: openapi.Response(
                description='List of upcoming events retrieved successfully',
                schema=EventListSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
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
        return Event.objects.filter(
            user=self.request.user
        ).select_related('space').order_by('-created_at')

    @swagger_auto_schema(
        operation_summary='List my events',
        operation_description='Get a list of all events created by the authenticated user',
        responses={
            200: openapi.Response(
                description='List of user events retrieved successfully',
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
            'message': f'Found {queryset.count()} events for user {request.user.username}',
            'count': queryset.count(),
            'events_by_status': events_by_status,
            'data': serializer.data
        })