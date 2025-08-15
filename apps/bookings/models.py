from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.spaces.models import Space

class Event(models.Model):
    event_name = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    start_date = models.DateField(null=True, blank=True, help_text="Start date for multi-day booking")
    end_date = models.DateField(null=True, blank=True, help_text="End date for multi-day booking")
    is_full_day = models.BooleanField(default=False, help_text="If checked, this is a full-day booking")
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
        now = timezone.now()
        if self.is_full_day:
            # For multi-day bookings, check the start date
            return self.status == 'confirmed' and self.start_date > now.date()
        else:
            # For standard time frame bookings, check the start datetime
            return self.status == 'confirmed' and self.start_datetime > now

    @property
    def event_status_display(self):
        """Get a human-readable status that includes timing information"""
        now = timezone.now()
        today = now.date()
        
        if self.status == 'confirmed':
            if self.is_full_day:
                # For multi-day bookings
                if self.start_date > today:
                    return 'Confirmed - Upcoming'
                elif self.end_date < today:
                    return 'Confirmed - Completed'
                else:
                    return 'Confirmed - In Progress'
            else:
                # For standard time frame bookings
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
        now = timezone.now()
        
        # For standard hourly booking (specific time frame)
        if not self.is_full_day and self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError('End datetime must be after start datetime')
            if self.start_datetime < now:
                raise ValidationError('Start datetime cannot be in the past')
        
        # For multi-day booking
        if self.is_full_day and self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError('End date must be after or equal to start date')
            if self.start_date < now.date():
                raise ValidationError('Start date cannot be in the past')

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
    start_date = models.DateField(null=True, blank=True, help_text="Start date for multi-day booking")
    end_date = models.DateField(null=True, blank=True, help_text="End date for multi-day booking")
    is_full_day = models.BooleanField(default=False, help_text="If checked, this is a full-day booking")
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
                name='start_datetime_before_end_datetime'
            ),
            models.CheckConstraint(
                check=models.Q(
                    models.Q(start_date__isnull=True) | 
                    models.Q(end_date__isnull=True) |
                    models.Q(start_date__lte=models.F('end_date'))
                ),
                name='start_date_before_end_date'
            )
        ]