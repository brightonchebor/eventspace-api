from django.contrib import admin
from .models import Event
# apps/bookings/admin.py
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'organizer_name', 'start_datetime', 'status')
    list_filter = ('status', 'event_type')
    search_fields = ('event_name', 'organizer_name', 'organizer_email')

