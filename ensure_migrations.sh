#!/bin/bash
# Script to ensure all apps have migrations

echo "Ensuring all Django apps have necessary migrations"

# Navigate to project root
cd "$(dirname "$0")"

# Create required directories first if they don't exist
mkdir -p apps/authentication/migrations
touch apps/authentication/migrations/__init__.py

mkdir -p apps/bookings/migrations
touch apps/bookings/migrations/__init__.py

mkdir -p apps/spaces/migrations
touch apps/spaces/migrations/__init__.py

mkdir -p apps/notifications/migrations
touch apps/notifications/migrations/__init__.py

mkdir -p apps/core/migrations
touch apps/core/migrations/__init__.py

# Generate migrations for each app
echo "Generating migrations for all apps..."
python manage.py makemigrations authentication
python manage.py makemigrations bookings
python manage.py makemigrations spaces
python manage.py makemigrations notifications
python manage.py makemigrations core

# Run a final check for any other migrations
python manage.py makemigrations

echo "Migration files created successfully."

# Show the status of migrations
echo "Migration status:"
python manage.py showmigrations

echo "Done! Your apps should now have all necessary migration files."
