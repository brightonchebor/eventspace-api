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
        help_text="Expected number of attendees",
        null=True,
        blank=True
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
            ('rejected', 'Rejected'),
        ],
        default='pending',
        help_text="Status of the event"
    )
    
    @property
    def is_upcoming(self):
        """Check if the event is upcoming (confirmed and in the future)"""
        return self.status == 'confirmed' and self.start_datetime > timezone.now()

    @property
    def event_status_display(self):
        """Get a human-readable status that includes timing information"""
        now = timezone.now()
        if self.status == 'confirmed':
            if self.start_datetime > now:
                return 'Confirmed - Upcoming'
            elif self.end_datetime < now:
                return 'Confirmed - Completed'
            else:
                return 'Confirmed - In Progress'
        return self.get_status_display()

    def __str__(self):
        return f"{self.event_name} ({self.event_status_display})"

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
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_name} - {self.space.name}"

    class Meta:
        ordering = ['start_datetime']

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('internal', 'Internal Event'),
        ('external', 'External Event'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]
    
    event_name = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    organizer_name = models.CharField(max_length=255)
    organizer_email = models.EmailField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    attendance = models.PositiveIntegerField(help_text="Expected number of attendees")
    required_resources = models.TextField(null=True, blank=True, help_text="Required resources for the event (comma separated)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.event_name} ({self.start_datetime.strftime('%Y-%m-%d')})"
        
    class Meta:
        ordering = ['-start_datetime']
        # Ensure no double bookings for the same space
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_datetime__lt=models.F('end_datetime')),
                name='start_before_end'
            )
        ]