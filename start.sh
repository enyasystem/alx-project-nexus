#!/usr/bin/env bash
set -euo pipefail

# Default PORT if not set by environment
: "${PORT:=8000}"

python manage.py migrate --noinput
python -m scripts.create_admin_if_missing
python manage.py collectstatic --noinput
exec gunicorn nexus.wsgi:application --bind 0.0.0.0:"$PORT" --workers 3
