Submission TODO (24h sprint)

Overview
- Goal: Prepare repo for submission for "E-Commerce Backend - ProDev BE". Focus on high-impact items that evaluators check.

Priority tasks (must do first)

- [ ] 1) Verify CI is green (tests, s3-smoke, preflight, publish-openapi) — 30–60m
  - Action: Open GitHub Actions, re-run failed workflows or inspect logs.

- [ ] 2) Quick functional smoke (local) — 30–60m
  - Commands:
    - python -m pytest -q
    - python manage.py runserver (manual) / use APIClient to exercise endpoints
  - Verify: register/login (JWT), CRUD products/categories, image upload, filter/sort/paginate

- [ ] 3) Publish API docs & link in README — 15–30m
  - Ensure .github/workflows/publish-openapi.yml runs and Redoc site is accessible.
  - Add link in README to published docs.

- [ ] 4) Confirm migrations + run instructions in README — 10–20m
  - Ensure migration files are committed and README has:
    - python manage.py migrate
    - python manage.py collectstatic --noinput
    - export USE_S3=0 or configure AWS secrets

- [ ] 5) Tag release and add short release notes — 10m
  - Commands:
    - git tag -a v1.0.0 -m "Release v1.0.0"
    - git push origin v1.0.0

Optional (if time remains)

- [ ] A) Replace coarse cache.clear() with targeted keys in signals — 30–60m
- [ ] B) Move from DEFAULT_FILE_STORAGE to STORAGES to remove deprecation warning — 20–40m
- [ ] C) Add Redis service to CI and run lockout integration test — 30–90m
- [ ] D) One-line runbook: enabling pg_trgm in production DB — 5m

Which item should I start now? I recommend starting with "Verify CI is green". If you approve, I will re-run failing workflows and fix anything that breaks.
