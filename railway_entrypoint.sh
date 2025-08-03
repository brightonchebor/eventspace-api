#!/bin/bash
# Railway entry point script

echo "Starting Railway deployment process..."

# Run migrations in correct order
echo "Running migrations in correct order..."
python manage.py migrate contenttypes --noinput
python manage.py migrate authentication --noinput 
python manage.py migrate --noinput

# Start the server
echo "Starting gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
