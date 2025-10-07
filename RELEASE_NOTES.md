Release v1.0.0 — E-Commerce Backend (ProDev BE)

Summary
- Final submission for the ProDev BE "E-Commerce Backend" project: a production-ready Django backend for a product catalog with authentication, media, and API docs.

Highlights
- CRUD APIs for Products and Categories with JWT authentication
- Product image upload (local + optional Amazon S3 via django-storages)
- Filtering, sorting, cursor pagination and trigram search optimization (Postgres)
- Password reset, email verification and cache-backed login lockout
- OpenAPI docs published to GitHub Pages (Redoc)
- CI: GitHub Actions with unit/integration tests, moto S3 smoke test, Redis lockout validation
- DB migrations included (pg_trgm migration guarded for Postgres)

Quick runbook
- Install deps: pip install -r requirements.txt
- Migrate: python manage.py migrate
- Run tests: python -m pytest -q
- Collect static: python manage.py collectstatic --noinput
- Dev server: python manage.py runserver

Production notes
- To enable S3 media: set USE_S3=1 and configure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME (or AWS_STORAGE_BUCKET_NAME). Prefer using IAM roles and CloudFront for public delivery.
- Trigram indexes: the migration creates pg_trgm and GIN trigram indexes on Postgres. If your DB user lacks CREATE EXTENSION, run: CREATE EXTENSION IF NOT EXISTS pg_trgm; (or run migrations with a privileged user).

Artifacts & links
- Release notes file: RELEASE_NOTES.md
- OpenAPI (Redoc): https://enyasystem.github.io/alx-project-nexus/
- Tests/CI: all checks passing on main

Changelog (high level)
- Added product image support + S3 optional backend
- Implemented JWT auth, registration + verification, password reset emails
- Added targeted cache invalidation + Redis lockout tests
- Added pg_trgm trigram GIN indexes (Postgres-only)
- CI workflows for tests, S3 smoke, docs publish, and Redis lockout
\n