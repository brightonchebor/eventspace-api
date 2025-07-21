from rest_framework import serializers
from .models import Event
from apps.spaces.models import Space
from apps.spaces.serializers import SpaceSerializer

class EventSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime',
            'organizer_name', 'status', 'space', 'space_name'
        ]
        read_only_fields = ['id', 'status', 'space_name']

    def validate(self, data):
        """
        Validate the event data
        """
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')

        # Validate datetime
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise serializers.ValidationError(
                    "End datetime must be after start datetime"
                )

        return data

class EventListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime',
            'status', 'space_name'
        ]