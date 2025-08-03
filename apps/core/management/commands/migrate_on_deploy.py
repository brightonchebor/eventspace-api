import os
import sys
import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = 'Runs migrations when the app is deployed on Railway'

    def handle(self, *args, **options):
        # Wait for database to be ready
        self.stdout.write('Waiting for database...')
        db_conn = None
        try:
            db_conn = connections['default']
        except OperationalError:
            self.stdout.write('Database unavailable, waiting 1 second...')
            time.sleep(1)
            
        # Check for Railway environment
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            self.stdout.write('Railway environment detected. Running migrations automatically.')
            call_command('makemigrations')
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS('Migrations successfully applied.'))
        else:
            self.stdout.write('Not running on Railway, skipping automatic migrations.')
