# ---- builder stage ----
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/app
COPY requirements.txt /tmp/app/
RUN python -m pip install --upgrade pip
# install into a temporary prefix so we can copy to final image
RUN python -m pip install --prefix=/install -r requirements.txt

# ---- runtime stage ----
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/usr/local/bin:$PATH

# create non-root user
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# copy installed python packages from builder
COPY --from=builder /install /usr/local

# copy application code
COPY . /app

# ensure start.sh is executable inside the image
RUN chmod +x /app/start.sh || true

# copy entrypoint and make executable
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# create static root directory and collect static at build time if possible; continue on failure
ENV DJANGO_SETTINGS_MODULE=nexus.settings
RUN mkdir -p /app/staticfiles \
 && chown -R app:app /app/staticfiles || true
RUN python manage.py collectstatic --noinput || true

# install gunicorn runtime
RUN python -m pip install --no-cache-dir gunicorn

# ensure correct ownership
RUN chown -R app:app /app

USER app

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "nexus.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
