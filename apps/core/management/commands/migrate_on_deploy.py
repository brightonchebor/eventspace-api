import os
import sys
import time
import pathlib
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError
from django.apps import apps

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
                # First ensure all migrations exist
                self.stdout.write('Ensuring all apps have migrations...')
                
                # Get all app configs
                app_configs = apps.get_app_configs()
                app_labels = [
                    app.label for app in app_configs 
                    if app.label.startswith('auth') or 
                       app.label in ['bookings', 'spaces', 'notifications', 'core']
                ]
                
                # Generate migrations for each app if models exist
                for app_label in app_labels:
                    try:
                        self.stdout.write(f'Checking migrations for {app_label}...')
                        call_command('makemigrations', app_label, interactive=False, verbosity=1)
                    except Exception as e:
                        self.stdout.write(f'Note: Could not generate migrations for {app_label}: {e}')
                
                # Final check for any other migrations
                call_command('makemigrations', interactive=False)
                
                # Step 1: Apply contenttypes migrations first
                self.stdout.write('Step 1: Applying contenttypes migrations...')
                call_command('migrate', 'contenttypes', interactive=False, verbosity=1)
                
                # Step 2: Apply auth migrations before our custom user model
                self.stdout.write('Step 2: Applying auth migrations...')
                call_command('migrate', 'auth', interactive=False, verbosity=1)
                
                # Step 3: Check if authentication app has migrations before applying
                auth_app_path = pathlib.Path(apps.get_app_config('authentication').path)
                auth_migration_path = auth_app_path / 'migrations'
                
                if auth_migration_path.exists():
                    migration_files = list(auth_migration_path.glob('*.py'))
                    has_auth_migrations = any(f for f in migration_files if f.name != '__init__.py')
                    
                    if has_auth_migrations:
                        self.stdout.write('Step 3: Applying authentication app migrations...')
                        call_command('migrate', 'authentication', interactive=False, verbosity=1)
                    else:
                        self.stdout.write('Step 3: No authentication migrations found to apply.')
                else:
                    self.stdout.write('Step 3: No migration directory for authentication app.')
                
                # Step 4: Apply all remaining migrations
                self.stdout.write('Step 4: Applying all remaining migrations...')
                call_command('migrate', interactive=False, verbosity=1)
                
                self.stdout.write(self.style.SUCCESS('Migrations successfully applied in correct order.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error applying migrations: {e}'))
        else:
            self.stdout.write('Not running on Railway, skipping automatic migrations.')
