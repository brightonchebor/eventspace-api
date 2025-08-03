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
        max_retries = 5
        retries = 0
        
        while retries < max_retries:
            try:
                db_conn = connections['default']
                db_conn.cursor()
                break
            except OperationalError:
                self.stdout.write(f'Database unavailable, waiting (attempt {retries+1}/{max_retries})...')
                retries += 1
                time.sleep(2)
        
        if retries >= max_retries:
            self.stdout.write(self.style.ERROR('Database connection failed after multiple attempts. Aborting migrations.'))
            return
            
        # Check for Railway environment
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            self.stdout.write('Railway environment detected. Running migrations in controlled order.')
            
            try:
                # Step 1: Apply contenttypes migrations first
                self.stdout.write('Step 1: Applying contenttypes migrations...')
                call_command('migrate', 'contenttypes', interactive=False, verbosity=1)
                
                # Step 2: Apply custom user model migrations
                self.stdout.write('Step 2: Applying authentication app migrations for custom user model...')
                call_command('migrate', 'authentication', interactive=False, verbosity=1)
                
                # Step 3: Apply all remaining migrations
                self.stdout.write('Step 3: Applying all remaining migrations...')
                call_command('migrate', interactive=False, verbosity=1)
                
                self.stdout.write(self.style.SUCCESS('Migrations successfully applied in correct order.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error applying migrations: {e}'))
        else:
            self.stdout.write('Not running on Railway, skipping automatic migrations.')
