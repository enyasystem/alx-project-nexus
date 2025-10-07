Security Incident Record

This document records the investigation and remediation steps for the secrets exposure.

Summary

- Date discovered: [26-09-2025]
- Discovered by: [Enya Elvis]
- Affected secrets: DJANGO_SECRET_KEY, POSTGRES_PASSWORD (example)
- Exposure: Committed to git history (private repo) — decision: history purge requested

Actions taken

1. Immediate rotation of affected credentials (timestamps):
   - DJANGO_SECRET_KEY rotated: [timestamp]
   - POSTGRES_PASSWORD rotated: [timestamp]
2. Updated GitHub Actions secrets: [timestamp]
3. Prepared purge plan: `PURGE_HISTORY.md`
4. Prepared purge-target list: `purge-targets.txt`
5. Prepared mirror creation helper: `scripts/prepare-git-mirror.ps1`
6. Prepared contributor notice: `Purge_Notice.md`

Planned next steps

- Execute purge during maintenance window: [date/time]
- Force-push rewritten history to origin
- Notify contributors and require reclone
- Rotate secrets again and validate services
- Monitor services for suspicious activity for 30 days

Postmortem notes

- Root cause: credentials were temporarily committed during local debugging and not removed before commit.
- Preventative measures:
  - Install pre-commit secret scanner
  - Add CI checks to block accidental secret exposure
  - Add documentation for secrets management

- Host environment override observed:
  - Symptom: after rotation the `web` container failed with "password authentication failed for user 'postgres'" despite `.env` being updated.
  - Cause: a host PowerShell environment variable `POSTGRES_PASSWORD` (value `ci-test-pass`) existed and docker-compose substituted that host env value for `${POSTGRES_PASSWORD}`.
  - Fix applied: updated `docker-compose.yml` to include `env_file: .env` for `db` and `web` and removed inline `${POSTGRES_PASSWORD}` substitution so the project's `.env` is authoritative. Recreated `web` so it picked up the rotated secret. Also removed the session host env var in PowerShell.
  - Recommendation: avoid host-level storage of sensitive credentials; prefer `env_file`, Docker secrets, or a secret manager. Add a short CI preflight that fails if suspicious host overrides are detected.

Contact

- Repo owner: enyasystem
- Security contact: [INSERT]
Rotation log (performed during purge)

- Second rotation performed: 2025-09-25T[REPLACE_WITH_TIME]Z
- GitHub Actions secrets updated: DJANGO_SECRET_KEY, POSTGRES_PASSWORD
- Deployment configs must be updated and services restarted (see `scripts/update-deployments.ps1`)

Verification

- CI run after rotation: pending manual trigger (run integration workflow to confirm)
