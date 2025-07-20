from django.contrib import admin
from .models import Event
from apps.notifications.views import send_booking_approved_notification

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'organizer_name', 'start_datetime', 'end_datetime', 'event_type', 'status', 'space')
    list_filter = ('status', 'event_type')
    search_fields = ('event_name', 'organizer_name', 'organizer_email')

    def save_model(self, request, obj, form, change):
        # Only send notification if status changed to 'confirmed'
        if change:
            old_obj = Event.objects.get(pk=obj.pk)
            if old_obj.status != 'confirmed' and obj.status == 'confirmed':
                # Call your notification function
                send_booking_approved_notification(obj, obj.space, obj.user)
        super().save_model(request, obj, form, change)

