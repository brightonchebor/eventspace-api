#!/bin/bash

# Script to run migrations in the correct order for Railway deployment
echo "Starting migration process for Railway deployment..."

# Step 1: Apply contenttypes migrations first
echo "Step 1: Applying contenttypes migrations..."
python manage.py migrate contenttypes --noinput

# Step 2: Apply custom user model migrations
echo "Step 2: Applying authentication app migrations for custom user model..."
python manage.py migrate authentication --noinput

# Step 3: Apply all remaining migrations
echo "Step 3: Applying all remaining migrations..."
python manage.py migrate --noinput

echo "Migration process completed successfully."
