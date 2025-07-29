from django.contrib import admin
from django.utils import timezone
from django.db.models import Q
from django.utils.html import format_html
from .models import Event
from apps.notifications.views import send_booking_approved_notification, send_booking_rejected_notification

# Define status choices as constants to ensure consistency
STATUS_PENDING = 'pending'
STATUS_CONFIRMED = 'confirmed'
STATUS_CANCELLED = 'cancelled'
STATUS_COMPLETED = 'completed'
STATUS_REJECTED = 'rejected'

class EventStatusFilter(admin.SimpleListFilter):
    title = 'Event Status'
    parameter_name = 'event_status'

    def lookups(self, request, model_admin):
        base_statuses = [
            (STATUS_PENDING, 'Pending Review'),
            (STATUS_CONFIRMED, 'All Confirmed'),
            ('upcoming', 'Upcoming Events'),  # Shows future confirmed events
            (STATUS_COMPLETED, 'Completed'),
            (STATUS_CANCELLED, 'Cancelled'),
            (STATUS_REJECTED, 'Rejected'),
        ]
        return base_statuses

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        now = timezone.now()
        value = self.value()

        if value == STATUS_CONFIRMED:
            # Show all events that admin has confirmed (including past events)
            return queryset.filter(
                status=STATUS_CONFIRMED
            ).order_by('-start_datetime')

        elif value == 'upcoming':
            # Only future confirmed events
            return queryset.filter(
                status=STATUS_CONFIRMED,
                start_datetime__gt=now
            ).order_by('start_datetime')

        elif value == STATUS_COMPLETED:
            # Show both explicitly completed events AND past confirmed events
            return queryset.filter(
                Q(status=STATUS_COMPLETED) |
                Q(status=STATUS_CONFIRMED, end_datetime__lt=now)
            ).order_by('-end_datetime')

        elif value == STATUS_PENDING:
            # Only pending events waiting for review
            return queryset.filter(
                status=STATUS_PENDING
            ).order_by('start_datetime')

        elif value in [STATUS_CANCELLED, STATUS_REJECTED]:
            return queryset.filter(
                status=value
            ).order_by('-created_at')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'status_with_badge', 'space', 'event_type',
                   'formatted_start_time', 'formatted_end_time', 
                   'organizer_name', 'time_until_event')
    list_display_links = ('event_name',)
    list_filter = (EventStatusFilter, 'event_type', 'space')
    search_fields = ('event_name', 'organizer_name', 'organizer_email')
    list_per_page = 20
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_completed']
    
    def is_upcoming_event(self, obj):
        """Indicates if this is an upcoming confirmed event"""
        return obj.is_upcoming
    is_upcoming_event.boolean = True
    is_upcoming_event.short_description = 'Upcoming'
    
    def time_until_event(self, obj):
        """Shows the time remaining until the event starts"""
        now = timezone.now()
        if obj.start_datetime > now:
            time_diff = obj.start_datetime - now
            days = time_diff.days
            hours = time_diff.seconds // 3600
            if days > 0:
                return f'In {days}d {hours}h'
            elif hours > 0:
                return f'In {hours}h'
            else:
                minutes = time_diff.seconds // 60
                return f'In {minutes}m'
        return 'Past event'
    time_until_event.short_description = 'Time Left'

    def status_with_badge(self, obj):
        """Display status with color-coded badge"""
        now = timezone.now()
        
        # Determine the actual status for display
        if obj.status == STATUS_CONFIRMED:
            if obj.end_datetime < now:
                status_display = 'Completed'
                color = 'info'
                bg_color = '#17a2b8'
            elif obj.start_datetime > now:
                status_display = 'Upcoming'
                color = 'success'
                bg_color = '#28a745'
            else:
                status_display = 'In Progress'
                color = 'success'
                bg_color = '#28a745'
        else:
            status_colors = {
                STATUS_PENDING: ('warning', '#ffc107', 'Pending'),
                STATUS_CANCELLED: ('danger', '#dc3545', 'Cancelled'),
                STATUS_COMPLETED: ('info', '#17a2b8', 'Completed'),
                STATUS_REJECTED: ('danger', '#dc3545', 'Rejected')
            }
            color, bg_color, status_display = status_colors.get(
                obj.status, 
                ('secondary', '#6c757d', obj.get_status_display())
            )
        
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px; '
            'border-radius: 10px; background-color: {}; color: white;">{}</span>',
            color, bg_color, status_display
        )
    status_with_badge.short_description = 'Status'
    status_with_badge.admin_order_field = 'status'

    def formatted_start_time(self, obj):
        return obj.start_datetime.strftime("%b %d, %Y %H:%M")
    formatted_start_time.short_description = 'Starts'
    formatted_start_time.admin_order_field = 'start_datetime'

    def formatted_end_time(self, obj):
        return obj.end_datetime.strftime("%b %d, %Y %H:%M")
    formatted_end_time.short_description = 'Ends'
    formatted_end_time.admin_order_field = 'end_datetime'

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Event.objects.get(pk=obj.pk)
            old_status = old_obj.status
            new_status = obj.status
            
            # Validate status transitions
            if old_status == STATUS_COMPLETED and new_status != STATUS_COMPLETED:
                # Don't allow changing completed events
                self.message_user(request, 'Completed events cannot be modified.', level='ERROR')
                obj.status = STATUS_COMPLETED
            
            elif old_status == STATUS_CANCELLED and new_status not in [STATUS_CANCELLED, STATUS_REJECTED]:
                # Don't allow reactivating cancelled events
                self.message_user(request, 'Cancelled events cannot be reactivated.', level='ERROR')
                obj.status = STATUS_CANCELLED
            
            elif old_status != STATUS_CONFIRMED and new_status == STATUS_CONFIRMED:
                # When confirming an event, check for conflicts
                conflicts = Event.objects.filter(
                    space=obj.space,
                    status=STATUS_CONFIRMED,
                    start_datetime__lt=obj.end_datetime,
                    end_datetime__gt=obj.start_datetime
                ).exclude(pk=obj.pk)
                
                if conflicts.exists():
                    self.message_user(
                        request,
                        'Cannot confirm event due to scheduling conflict.',
                        level='ERROR'
                    )
                    obj.status = old_status
                else:
                    # Send confirmation notification
                    super().save_model(request, obj, form, change)
                    send_booking_approved_notification(obj, obj.space, obj.user)
                    self.message_user(
                        request,
                        'Event confirmed successfully and notification sent.',
                        level='SUCCESS'
                    )
                    return
            
            elif new_status == STATUS_COMPLETED and obj.end_datetime > timezone.now():
                # Don't allow marking future events as completed
                self.message_user(
                    request,
                    'Cannot mark future events as completed.',
                    level='ERROR'
                )
                obj.status = old_status
        
        # Send rejection email if status changed to 'rejected'
        if change:
            old_obj = Event.objects.get(pk=obj.pk)
            # Send rejection email if status changed to 'rejected'
            if old_obj.status != 'rejected' and obj.status == 'rejected':
                send_booking_rejected_notification(obj, obj.space, obj.user)
        
        super().save_model(request, obj, form, change)

    def mark_as_confirmed(self, request, queryset):
        now = timezone.now()
        success_count = 0
        error_count = 0
        
        for event in queryset.filter(status=STATUS_PENDING):
            # Check for conflicts
            conflicts = Event.objects.filter(
                space=event.space,
                status=STATUS_CONFIRMED,
                start_datetime__lt=event.end_datetime,
                end_datetime__gt=event.start_datetime
            ).exclude(pk=event.pk)
            
            if conflicts.exists():
                error_count += 1
                self.message_user(
                    request,
                    f'Cannot confirm "{event.event_name}" due to scheduling conflict.',
                    level='ERROR'
                )
            else:
                event.status = STATUS_CONFIRMED
                event.save()
                send_booking_approved_notification(event, event.space, event.user)
                success_count += 1
        
        if success_count > 0:
            self.message_user(
                request,
                f'{success_count} events were confirmed successfully.',
                level='SUCCESS'
            )
        if error_count > 0:
            self.message_user(
                request,
                f'{error_count} events could not be confirmed due to conflicts.',
                level='WARNING'
            )
    mark_as_confirmed.short_description = 'Confirm selected events'

    def mark_as_cancelled(self, request, queryset):
        # Can't cancel completed events
        non_completed = queryset.exclude(status=STATUS_COMPLETED)
        skipped = queryset.filter(status=STATUS_COMPLETED).count()
        updated = non_completed.update(status=STATUS_CANCELLED)
        
        if updated > 0:
            self.message_user(request, f'{updated} events were cancelled.', level='SUCCESS')
        if skipped > 0:
            self.message_user(
                request,
                f'{skipped} completed events were skipped.',
                level='WARNING'
            )
    mark_as_cancelled.short_description = 'Cancel selected events'

    def mark_as_completed(self, request, queryset):
        now = timezone.now()
        # Only complete confirmed events that have ended
        completable = queryset.filter(
            status=STATUS_CONFIRMED,
            end_datetime__lt=now
        )
        updated = completable.update(status=STATUS_COMPLETED)
        skipped = queryset.count() - updated
        
        if updated > 0:
            self.message_user(request, f'{updated} events were marked as completed.', level='SUCCESS')
        if skipped > 0:
            self.message_user(
                request,
                f'{skipped} events were skipped (not confirmed or not ended yet).',
                level='WARNING'
            )
    mark_as_completed.short_description = 'Mark ended events as completed'

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

