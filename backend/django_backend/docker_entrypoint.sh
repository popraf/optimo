#!/bin/sh
set -e  # Exit immediately if a command exits with a non-zero status.

echo "Collect static files"
python manage.py collectstatic --noinput

# Execute the default command passed as arguments
exec "$@"
