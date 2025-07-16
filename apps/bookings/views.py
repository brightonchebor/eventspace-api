from django.shortcuts import render
from django.utils import timezone
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Event
from .serializers import EventSerializer, EventListSerializer


class BookEventView(CreateAPIView):
    """
    Book a new event
    """
    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Book a new event',
        operation_description='Create a new event booking with the provided details',
        request_body=EventSerializer,
        responses={
            201: openapi.Response(
                description='Event booked successfully',
                schema=EventSerializer
            ),
            400: openapi.Response(
                description='Bad request - validation errors',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Automatically assign the current user
            event = serializer.save(user=request.user)
            
            return Response({
                'message': f'Event "{event.event_name}" has been booked successfully',
                'data': serializer.data
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter events to show only upcoming ones (start_datetime is in the future)
        """
        return Event.objects.filter(
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')

    @swagger_auto_schema(
        operation_summary='List upcoming events',
        operation_description='Get a list of all upcoming events ordered by start date',
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description='Filter events by status (pending, confirmed, cancelled)',
                type=openapi.TYPE_STRING,
                enum=['pending', 'confirmed', 'cancelled']
            ),
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
                description='List of upcoming events retrieved successfully',
                schema=EventListSerializer(many=True)
            )
        }
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Optional filtering by event type
        event_type_filter = request.query_params.get('event_type', None)
        if event_type_filter:
            queryset = queryset.filter(event_type=event_type_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'message': 'Upcoming events retrieved successfully',
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ListMyEventsView(ListAPIView):
    """
    List events created by the current user
    """
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter events to show only those created by the current user
        """
        return Event.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @swagger_auto_schema(
        operation_summary='List my events',
        operation_description='Get a list of events created by the current user',
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
        
        return Response({
            'message': 'Your events retrieved successfully',
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)