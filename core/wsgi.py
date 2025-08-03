"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

# Run migrations automatically on Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    try:
        print("Railway deployment detected. Running migrations automatically...")
        # Make sure command modules are in the path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        call_command('migrate')
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error applying migrations: {e}")
