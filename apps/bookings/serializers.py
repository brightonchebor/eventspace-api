from rest_framework import serializers
from django.utils import timezone
from .models import Event
from apps.spaces.models import Space


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime', 
            'organizer_name', 'organizer_email', 'event_type', 
            'attendance', 'status', 'space'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Custom validation for event booking
        """
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        space = data.get('space')
        attendance = data.get('attendance')

        # Check if start time is in the future
        if start_datetime and start_datetime <= timezone.now():
            raise serializers.ValidationError({
                'start_datetime': 'Event start time must be in the future.'
            })

        # Check if end time is after start time
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise serializers.ValidationError({
                'end_datetime': 'Event end time must be after start time.'
            })

        # Check if space capacity is sufficient
        if space and attendance and attendance > space.capacity:
            raise serializers.ValidationError({
                'attendance': f'Attendance ({attendance}) exceeds space capacity ({space.capacity}).'
            })

        # Check for conflicting events in the same space
        if space and start_datetime and end_datetime:
            conflicting_events = Event.objects.filter(
                space=space,
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime,
                status__in=['pending', 'confirmed']
            )
            
            # Exclude current event if updating
            if self.instance:
                conflicting_events = conflicting_events.exclude(id=self.instance.id)
            
            if conflicting_events.exists():
                raise serializers.ValidationError({
                    'space': 'This space is already booked for the selected time period.'
                })

        return data


class EventListSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    space_location = serializers.CharField(source='space.location', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'start_datetime', 'end_datetime',
            'organizer_name', 'organizer_email', 'event_type',
            'attendance', 'status', 'space', 'space_name', 
            'space_location', 'user_name', 'created_at'
        ]