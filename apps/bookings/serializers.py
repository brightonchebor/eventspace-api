from rest_framework import serializers
from .models import Event
from apps.spaces.models import Space
from apps.spaces.serializers import SpaceSerializer

class EventSerializer(serializers.ModelSerializer):
    space_details = SpaceSerializer(source='space', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime',
            'organizer_name', 'organizer_email', 'event_type',
            'attendance', 'status', 'space', 'space_details',
            'user_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'user_name']

    def validate(self, data):
        """
        Validate the event data
        """
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        space = data.get('space')
        attendance = data.get('attendance')

        # Validate datetime
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise serializers.ValidationError(
                    "End datetime must be after start datetime"
                )

        # Validate space capacity
        if space and attendance:
            if attendance > space.capacity:
                raise serializers.ValidationError(
                    f"Attendance ({attendance}) exceeds space capacity ({space.capacity})"
                )

        return data

class EventListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    space_location = serializers.CharField(source='space.location', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime',
            'organizer_name', 'event_type', 'attendance', 'status',
            'space_name', 'space_location', 'user_name', 'created_at'
        ]