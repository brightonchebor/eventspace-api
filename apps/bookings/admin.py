from django.contrib import admin
from django.utils import timezone
from .models import Event
from apps.notifications.views import send_booking_approved_notification

class EventStatusFilter(admin.SimpleListFilter):
    title = 'Event Status'
    parameter_name = 'event_status'

    def lookups(self, request, model_admin):
        return (
            ('confirmed', 'Confirmed'),
            ('upcoming', 'Upcoming'),
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('rejected', 'Rejected'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'upcoming':
            return queryset.filter(status='confirmed', start_datetime__gt=now)
        elif self.value() == 'confirmed':
            return queryset.filter(status='confirmed')
        elif self.value():
            return queryset.filter(status=self.value())

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'organizer_name', 'start_datetime', 'end_datetime', 
                   'event_type', 'status', 'space', 'is_upcoming_event')
    list_filter = ('event_type', EventStatusFilter)
    search_fields = ('event_name', 'organizer_name', 'organizer_email')
    
    def is_upcoming_event(self, obj):
        return obj.is_upcoming
    is_upcoming_event.boolean = True
    is_upcoming_event.short_description = 'Upcoming'

    def save_model(self, request, obj, form, change):
        # Only send notification if status changed to 'confirmed'
        if change:
            old_obj = Event.objects.get(pk=obj.pk)
            if old_obj.status != 'confirmed' and obj.status == 'confirmed':
                # Call your notification function
                send_booking_approved_notification(obj, obj.space, obj.user)
        super().save_model(request, obj, form, change)

