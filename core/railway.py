"""
Railway-specific settings that override the base settings.
This file is automatically loaded by manage.py when running on Railway.
"""

from .settings import *

# Ensure DEBUG is off in production
DEBUG = False

# Remove Jazzmin from installed apps to prevent theme-related errors
if 'jazzmin' in INSTALLED_APPS:
    INSTALLED_APPS.remove('jazzmin')

# Use Django's default admin interface
JAZZMIN_SETTINGS = {}
JAZZMIN_UI_TWEAKS = {}

# Ensure Railway domain is in allowed hosts
if 'eventspace-api-production.up.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('eventspace-api-production.up.railway.app')

# Add more production-specific settings here if needed
SECURE_SSL_REDIRECT = False  # Set to True if Railway provides SSL
SESSION_COOKIE_SECURE = False  # Set to True if Railway provides SSL
CSRF_COOKIE_SECURE = False  # Set to True if Railway provides SSL

# Make sure static files are properly configured
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
