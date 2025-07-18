from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.spaces.models import Space

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
            ('cancelled', 'Cancelled'),
            ('completed', 'Completed'),
            ('upcoming', 'Upcoming'),
            ('rejected', 'Rejected'),
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
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="Space where the event will be held"
    )

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError('End datetime must be after start datetime')
            if self.start_datetime < timezone.now():
                raise ValidationError('Start datetime cannot be in the past')

    def save(self, *args, **kwargs):
        self.clean()
        
        # Auto-set status to upcoming if confirmed and in the future
        if self.status == 'confirmed' and self.start_datetime > timezone.now():
            self.status = 'upcoming'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_name} - {self.space.name}"

    class Meta:
        ordering = ['start_datetime']