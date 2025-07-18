import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create the Celery app
app = Celery('eventspace')

# Use a string here instead of a direct import so that the app is configurable
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Define periodic tasks
app.conf.beat_schedule = {
    'update-space-status-every-5-minutes': {
        'task': 'apps.bookings.tasks.update_space_status',
        'schedule': 300.0,  # every 5 minutes
    },
    'check-pending-events-every-hour': {
        'task': 'apps.bookings.tasks.check_pending_events',
        'schedule': 3600.0,  # every hour
    },
}

app.conf.timezone = 'Africa/Nairobi'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
