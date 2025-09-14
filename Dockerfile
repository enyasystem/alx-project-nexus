FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install python dependencies
COPY requirements.txt /code/
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /code/

# Collect static files (optional)
ENV DJANGO_SETTINGS_MODULE=nexus.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python manage.py collectstatic --noinput || true

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
