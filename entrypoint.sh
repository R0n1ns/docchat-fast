#!/bin/bash

# Wait for the database to be ready
echo "Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Initialize the database
python init_db.py

# Start the application
exec "$@"