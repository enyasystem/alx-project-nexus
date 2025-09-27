# Project Nexus Documentation

## Overview
This repository documents major learnings from the ProDev Backend Engineering program.
It serves as a knowledge hub for backend technologies, concepts, challenges, and best practices covered during the program.

## Objectives
- Consolidate key learnings from the ProDev Backend Engineering program.
- Document backend technologies, concepts, challenges, and solutions.
- Provide a reference guide for current and future learners.
- Support collaboration between frontend and backend learners.

## Key Technologies
- Python
- Django
- REST APIs
- GraphQL
- Docker
- CI/CD Pipelines

## Backend Concepts
- Database Design
- Asynchronous Programming
- Caching Strategies
- System Design

## Challenges and Solutions
- Managing long-running tasks → Solved with Celery and RabbitMQ
- Database performance issues → Solved with query optimization and indexing
- Deployment difficulties → Solved with Docker and automated CI/CD pipelines

## Best Practices and Takeaways
- Write clean and modular code
- Document APIs clearly
- Use version control effectively
- Apply security measures consistently

## Collaboration
This project encourages collaboration with:
- Backend learners for sharing knowledge and solving problems
- Frontend learners who will use backend endpoints

Communication and collaboration are supported through the **#ProDevProjectNexus** Discord channel.

## Repository
GitHub Repository: **alx-project-nexus**

## Getting started (local dev)

This repo contains a Django project (`nexus`) and a `catalog` app implementing the product catalog APIs.


Performance profiling
---------------------

There is a small helper script at `scripts/seed_and_profile.py` to seed products and profile the product-list endpoint.

Run it after starting a dev server (Postgres recommended for realistic results):

```powershell
& .\venv\Scripts\Activate.ps1
# Seed via Django shell (1000 products)
python manage.py shell -c "import scripts.seed_and_profile as s; s.seed(1000)"
# Or run the script which will attempt to seed then profile
python scripts/seed_and_profile.py --host http://localhost:8000 --count 1000
```

The script prints simple latency stats (avg/min/max) for multiple iterations.

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Run migrations and start the dev server (uses SQLite by default; to use PostgreSQL set `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` in a `.env` file):

```powershell
python manage.py migrate
python manage.py runserver
```

API docs (Swagger UI) will be available at `http://127.0.0.1:8000/api/docs/`.

Seeding the database (local dev)

1. Activate your virtualenv and install deps:

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the seed command to populate sample data:

```powershell
python manage.py seed
```

Docker Compose (Postgres + Django)

Start services with Docker Compose (requires Docker):

```powershell
docker compose up --build
```

The Django app will run at `http://127.0.0.1:8000` and Postgres at `localhost:5432`.

CI Secrets
----------

This repository expects database and secret values to be provided via GitHub Actions secrets for CI jobs. Set the following in `Settings → Secrets → Actions` for the repository:

- `POSTGRES_PASSWORD` — password for the CI Postgres service
- `DJANGO_SECRET_KEY` — Django secret key for CI (use a random 50+ character value)

Rotation guidance
-----------------

If any secret was accidentally committed, rotate it immediately:

1. Generate a new secret value (DB password, API key, etc.).
2. Update the service (rotate DB user/password in your Postgres host or managed DB).
3. Update the corresponding GitHub Actions secret value.
4. Re-run CI to ensure jobs succeed with the new secret.
5. Optionally, remove the old value from git history using `git filter-repo` or BFG (coordinate with collaborators). Always rotate credentials even after history rewrite.

Docker build notes

- A `Dockerfile` and `.dockerignore` are included to build the web image.
- To build locally run (requires Docker):

```powershell
docker compose build web
docker compose up web
```

- If you see a connection error when building, ensure Docker Desktop or the Docker daemon is running.

Profiling with Docker Compose
----------------------------

After starting the stack with `docker compose up --build`, seed the database and run the profiling script from within the web container or from your host targeting the running server. Example (host):

```powershell
# wait for migrations to finish, then on host
python scripts/seed_and_profile.py --host http://localhost:8000 --count 1000
```

Integration tests & CI
----------------------

A minimal integration smoke test is included at `tests/integration/test_smoke_db.py`. It verifies the database connection and that a health endpoint responds.

Run the smoke tests locally (after migrations):

```powershell
python manage.py migrate
python -m pytest tests/integration/test_smoke_db.py
```

To run the integration workflow on GitHub Actions, ensure the following repository secrets are set in `Settings → Secrets → Actions`:

- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`

You can trigger the workflow manually from the Actions tab (`workflow_dispatch`) or by pushing changes to the branch.

## Media storage (optional: Amazon S3)

This project supports storing uploaded media (product images) either on local disk in development or on Amazon S3 in production via `django-storages`.

Quick setup (development - local media):

- Ensure `MEDIA_ROOT` and `MEDIA_URL` are set (already configured in `nexus/settings.py`).
- During development run the dev server; uploaded files will be stored under `mediafiles/`.

Quick setup (production - S3):

1. Install dependencies:

```bash
pip install boto3 django-storages
```

2. Set the following environment variables in your deployment environment:

- `USE_S3=1`  # enable S3-backed media
- `AWS_S3_BUCKET_NAME` — the S3 bucket name for media
- `AWS_ACCESS_KEY_ID` — IAM access key ID
- `AWS_SECRET_ACCESS_KEY` — IAM secret access key
- `AWS_S3_REGION_NAME` — AWS region (optional)
- `AWS_S3_CUSTOM_DOMAIN` — optional custom domain for your bucket

3. Confirm `DEFAULT_FILE_STORAGE` uses `storages.backends.s3boto3.S3Boto3Storage` when `USE_S3=1` (this is handled by `nexus/settings.py`).

Security and considerations

- Use a restricted IAM user with only the permissions required for S3 PutObject/GetObject/ListBucket on the media bucket.
- Use an object lifecycle and bucket policy to control public access if needed.
- Consider using a CDN (CloudFront) in front of the S3 bucket for improved performance and caching.

Example IAM policy (least privilege)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3AccessForMediaBucket",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-media-bucket",
        "arn:aws:s3:::your-media-bucket/*"
      ]
    }
  ]
}
```

Notes:
- Replace `your-media-bucket` with the intended S3 bucket name.
- If using CloudFront, prefer to restrict bucket access via an Origin Access Identity (OAI) or Origin Access Control (OAC) instead of making the bucket publicly readable.
- Do not store credentials in the repository; use secrets managers or environment variables.

Deployment checklist for S3

- Create a dedicated S3 bucket for media.
- Configure bucket policy to block public access unless intentionally serving public assets.
- Create an IAM user or role scoped to the bucket using the policy above.
- Configure `USE_S3=1` and provide `AWS_*` env vars in the deployment environment.
- If using CloudFront, use a custom domain and set `AWS_S3_CUSTOM_DOMAIN` to the distribution domain.

Verify

- After deployment, upload a product image via the API and confirm the file appears in the S3 bucket and that the `image` field in API responses contains the expected URL.
