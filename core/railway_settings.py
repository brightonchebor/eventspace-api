"""
Railway-specific settings that override the base settings when running on Railway.
"""

import os
from .settings import *

# Override settings for Railway deployment
RAILWAY_ENVIRONMENT = True
DEBUG = False

# Remove Jazzmin from INSTALLED_APPS to fix admin interface issues
if 'jazzmin' in INSTALLED_APPS:
    INSTALLED_APPS.remove('jazzmin')

# Reset Jazzmin settings to avoid theme errors
JAZZMIN_SETTINGS = {}
JAZZMIN_UI_TWEAKS = {}

# Database connection uses Railway-provided PostgreSQL credentials
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE"),
        "USER": os.environ.get("PGUSER"),
        "PASSWORD": os.environ.get("PGPASSWORD"),
        "HOST": os.environ.get("PGHOST"),
        "PORT": os.environ.get("PGPORT"),
    }
}

# Security settings for production
SECURE_SSL_REDIRECT = False  # Set to True if Railway provides SSL
SESSION_COOKIE_SECURE = False  # Set to True if Railway provides SSL
CSRF_COOKIE_SECURE = False  # Set to True if Railway provides SSL

# Add Railway domain to allowed hosts
railway_domain = os.environ.get('RAILWAY_DOMAIN')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
    ALLOWED_HOSTS.append(f"*.{railway_domain}")

# Railway static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Railway media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Set site URL for absolute URLs
SITE_URL = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'https://your-app.up.railway.app')

# Disable Django's handling of static files
# Let whitenoise handle it
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Log to console on Railway
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
