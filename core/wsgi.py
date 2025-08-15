"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import pathlib

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

# Run migrations automatically on Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    try:
        print("Railway deployment detected. Running migrations in controlled order...")
        # Make sure command modules are in the path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # First generate migrations if needed
        print("Checking for missing migrations...")
        try:
            call_command('makemigrations', 'authentication', interactive=False)
            call_command('makemigrations', 'bookings', interactive=False)
            call_command('makemigrations', 'spaces', interactive=False)
            call_command('makemigrations', 'notifications', interactive=False)
            call_command('makemigrations', interactive=False)
        except Exception as make_err:
            print(f"Note: Error during makemigrations (non-critical): {make_err}")
        
        # Apply migrations in correct order to avoid dependencies issues
        print("Step 1: Apply contenttypes migrations")
        call_command('migrate', 'contenttypes', interactive=False)
        
        # Check if authentication has migrations before trying to apply them
        auth_migration_path = pathlib.Path(__file__).parent.parent / 'apps' / 'authentication' / 'migrations'
        has_auth_migrations = False
        
        if auth_migration_path.exists():
            migration_files = list(auth_migration_path.glob('*.py'))
            has_auth_migrations = any(f for f in migration_files if f.name != '__init__.py')
        
        if has_auth_migrations:
            print("Step 2: Apply authentication migrations")
            call_command('migrate', 'authentication', interactive=False)
        else:
            print("Step 2: No authentication migrations to apply")
        
        print("Step 3: Apply remaining migrations")
        call_command('migrate', interactive=False)
        
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error applying migrations: {e}")
        # Wait a bit before failing to ensure log is written
        time.sleep(2)
