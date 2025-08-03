#!/bin/bash
# Railway entry point script

echo "Starting Railway deployment process..."

# Set Django settings to Railway-specific module
export DJANGO_SETTINGS_MODULE=core.railway_settings
export RAILWAY_ENVIRONMENT=production

# Ensure migration directories exist
echo "Ensuring migration directories..."
mkdir -p apps/authentication/migrations
touch apps/authentication/migrations/__init__.py

mkdir -p apps/bookings/migrations
touch apps/bookings/migrations/__init__.py

mkdir -p apps/spaces/migrations
touch apps/spaces/migrations/__init__.py

mkdir -p apps/notifications/migrations
touch apps/notifications/migrations/__init__.py

# First, generate migrations if needed
echo "Checking and generating migrations if needed..."
python manage.py makemigrations authentication --noinput
python manage.py makemigrations bookings --noinput
python manage.py makemigrations spaces --noinput
python manage.py makemigrations notifications --noinput
python manage.py makemigrations --noinput

# Show migrations status for debugging
echo "Current migration status:"
python manage.py showmigrations --list

# Run migrations in correct order
echo "Running migrations in correct order..."

# Step 1: Apply contenttypes and auth migrations first
echo "Step 1: Applying contenttypes and auth migrations..."
python manage.py migrate contenttypes --noinput
python manage.py migrate auth --noinput

# Step 2: Check if authentication app has migrations
if [ -d "apps/authentication/migrations" ] && [ "$(ls -A apps/authentication/migrations/*.py 2>/dev/null | grep -v __init__.py)" ]; then
    echo "Step 2: Applying authentication migrations..."
    python manage.py migrate authentication --noinput
else
    echo "Step 2: No authentication migrations to apply."
    # If no migrations exist but models do, force creation of initial migration
    if grep -q "class.*model" apps/authentication/models.py 2>/dev/null; then
        echo "Authentication models detected. Forcing initial migration creation..."
        python manage.py makemigrations authentication --empty --name initial
        python manage.py migrate authentication --noinput
    fi
fi

# Step 3: Apply all remaining migrations
echo "Step 3: Applying all remaining migrations..."
python manage.py migrate --noinput

# Start the server
echo "Starting gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000}
