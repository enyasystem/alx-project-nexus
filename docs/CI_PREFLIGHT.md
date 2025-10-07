CI preflight checks and troubleshooting
=====================================

This document explains how to run the lightweight CI "preflight" checks locally and what the GitHub Actions `preflight` job does.

Why this exists
----------------
- Prevents long CI runs from starting when required secrets are missing or obviously misconfigured.
- Detects a common local footgun where host environment variables silently override docker-compose interpolation.

What the preflight job checks
-----------------------------
- Required secrets: `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY` are present in the runtime environment (Actions secrets or local `.env`).
- Prints a sanitized `docker-compose` configuration so you can quickly verify what will be used in CI.

Local preflight (fast)
----------------------
1. Ensure you have a project `.env` file at the repo root (example: `.env.example` contains placeholders).
2. The check is a simple script you can run locally from PowerShell:

```powershell
Set-Location 'C:\Users\HP PC\Documents\Project Nexus'
$envFile = Join-Path (Get-Location) '.env'
if (-Not (Test-Path $envFile)) { Write-Error ".env missing — copy .env.example to .env and fill values"; exit 1 }

# quick check for the two critical secrets
$dotenv = Get-Content $envFile | Where-Object { $_ -and -not ($_ -match '^\s*#') } | ForEach-Object {
  $k,v = $_ -split '=',2; @{ Key = $k.Trim(); Value = $v.Trim() }
}
$has_db_pass = $dotenv | Where-Object { $_.Key -eq 'POSTGRES_PASSWORD' -and $_.Value } | Measure-Object | Select-Object -ExpandProperty Count
$has_django_key = $dotenv | Where-Object { $_.Key -eq 'DJANGO_SECRET_KEY' -and $_.Value } | Measure-Object | Select-Object -ExpandProperty Count
if ($has_db_pass -eq 0) { Write-Error 'POSTGRES_PASSWORD is missing or empty in .env'; exit 2 }
if ($has_django_key -eq 0) { Write-Error 'DJANGO_SECRET_KEY is missing or empty in .env'; exit 3 }

Write-Host 'Local preflight passed — secrets present in .env'

# Optional: show the interpolated compose config with secrets masked
docker-compose config | ForEach-Object { $_ -replace ($env:POSTGRES_PASSWORD), '****' } | Out-String
```

Notes:
- The local script above assumes Docker Compose is available on your machine and that `.env` contains the entries. It purposefully masks the `POSTGRES_PASSWORD` when printing.

GitHub Actions preflight behavior
--------------------------------
- The `preflight` job in `.github/workflows/integration.yml` verifies repository secrets are present in the Actions runtime. It fails fast if any required secret is missing.
- It also attempts to print a sanitized `docker-compose config` (if docker-compose is available on the runner) to help debugging.

Common failures and fixes
CI preflight checks and troubleshooting
=====================================

This document explains how to run the lightweight CI "preflight" checks locally and what the GitHub Actions `preflight` job does.

Why this exists
----------------
- Prevents long CI runs from starting when required secrets are missing or obviously misconfigured.
- Detects a common local footgun where host environment variables silently override docker-compose interpolation.

What the preflight job checks
-----------------------------
- Required secrets: `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY` are present in the runtime environment (Actions secrets or local `.env`).
- Prints a sanitized `docker-compose` configuration so you can quickly verify what will be used in CI.

Local preflight (fast)
----------------------
1. Ensure you have a project `.env` file at the repo root (example: `.env.example` contains placeholders).
2. The check is a simple script you can run locally from PowerShell:

```powershell
Set-Location 'C:\Users\HP PC\Documents\Project Nexus'
$envFile = Join-Path (Get-Location) '.env'
if (-Not (Test-Path $envFile)) { Write-Error ".env missing — copy .env.example to .env and fill values"; exit 1 }

# quick check for the two critical secrets
$dotenv = Get-Content $envFile | Where-Object { $_ -and -not ($_ -match '^\s*#') } | ForEach-Object {
  $k,v = $_ -split '=',2; @{ Key = $k.Trim(); Value = $v.Trim() }
}
$has_db_pass = $dotenv | Where-Object { $_.Key -eq 'POSTGRES_PASSWORD' -and $_.Value } | Measure-Object | Select-Object -ExpandProperty Count
$has_django_key = $dotenv | Where-Object { $_.Key -eq 'DJANGO_SECRET_KEY' -and $_.Value } | Measure-Object | Select-Object -ExpandProperty Count
if ($has_db_pass -eq 0) { Write-Error 'POSTGRES_PASSWORD is missing or empty in .env'; exit 2 }
if ($has_django_key -eq 0) { Write-Error 'DJANGO_SECRET_KEY is missing or empty in .env'; exit 3 }

Write-Host 'Local preflight passed — secrets present in .env'

# Optional: show the interpolated compose config with secrets masked
docker-compose config | ForEach-Object { $_ -replace ($env:POSTGRES_PASSWORD), '****' } | Out-String
```

Notes:
- The local script above assumes Docker Compose is available on your machine and that `.env` contains the entries. It purposefully masks the `POSTGRES_PASSWORD` when printing.

GitHub Actions preflight behavior
--------------------------------
- The `preflight` job in `.github/workflows/integration.yml` verifies repository secrets are present in the Actions runtime. It fails fast if any required secret is missing.
- It also attempts to print a sanitized `docker-compose config` (if docker-compose is available on the runner) to help debugging.

Common failures and fixes
------------------------
- Failure: "POSTGRES_PASSWORD is missing" — In Actions: set `POSTGRES_PASSWORD` in repository secrets. Locally: create `.env` with `POSTGRES_PASSWORD=` filled.
- Failure: Host env vars override compose interpolation — Unset any session-level or system-level `POSTGRES_PASSWORD` or other POSTGRES_* variables; prefer `.env` + `env_file` instead of relying on shell interpolation.
- Failure: `docker-compose: command not found` in preflight — the runner image may not include docker-compose. This is non-fatal for the preflight step; it simply won't print the composed config. The integration job still runs in a separate runner that has service containers.

What to do if preflight passes but integration fails
----------------------------------------------------
- Inspect the integration job logs (they contain the service container init logs). Common issue: the Postgres service needs `POSTGRES_PASSWORD` present in the service env in Actions so the container can initialize.
- If you see "Database is uninitialized and superuser password is not specified", update `.github/workflows/integration.yml` to ensure the `db` service has `POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}` in its `env` block.

Quick checklist before pushing changes that affect CI
----------------------------------------------------
- Update `.env.example` and `SECURITY_INCIDENT.md` if you rotate secrets.
- Run the local preflight script above and verify it passes.
- Push changes to a feature branch and confirm the `preflight` job in GitHub Actions passes before relying on the longer `integration` job.

Contact
-------
- If you need help interpreting CI logs or fixing a failing preflight, attach the sanitized `docker-compose config` output (it will be included in the preflight logs when available) and I can help interpret it.

End of document
\n
