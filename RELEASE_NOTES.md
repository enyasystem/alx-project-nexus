Release v1.0.0 — E-Commerce Backend - ProDev BE

Summary
- Final submission for the ProDev BE E-Commerce Backend project.

Highlights
- Product and Category CRUD APIs with JWT authentication
- Product image upload support (local and optional S3 integration)
- Filtering, sorting, and pagination for product discovery
- OpenAPI (drf-spectacular) documentation with published Redoc workflow
- Database performance improvements: indexes and PostgreSQL trigram search
- Password reset, email verification, and account lockout protections
- CI: GitHub Actions with s3-smoke moto test, pre-commit, and docs validation

Runbook (quick)
- Migrate: python manage.py migrate
- Run tests: python -m pytest -q
- Collect static: python manage.py collectstatic --noinput
- To use S3 in production: set USE_S3=1 and configure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME in environment or GitHub secrets.

Changelog
- See commit history for detailed changes.
