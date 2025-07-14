from django.db import models
from django.conf import settings

class Event(models.Model):
    event_name = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    organizer_name = models.CharField(max_length=100)
    organizer_email = models.EmailField()
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('meeting', 'Meeting'),
            ('conference', 'Conference'),
            ('webinar', 'Webinar'),
            ('workshop', 'Workshop'),
        ],
        default='meeting',
        help_text="Type of event being booked"
    )
    attendance = models.PositiveIntegerField(
        help_text="Expected number of attendees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,      
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled')
        ],
        default='pending',
        help_text="Status of the event"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="User who created the event"
    )
    space = models.CharField(
        max_length=100,
        blank=True,
        help_text="Venue or location of the event"
    )

    def __str__(self):
        return self.event_name            ('other', 'Other')
