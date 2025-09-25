Pre-commit and secret scanning
==============================

This project uses `pre-commit` and `detect-secrets` to catch accidental secrets before they are committed.

Local setup (Windows PowerShell)
--------------------------------
From the repository root run:

```powershell
./scripts/setup-precommit.ps1
```

This installs `pre-commit` and `detect-secrets`, installs the git hooks, and creates a `.secrets.baseline` that you should inspect and commit.

Using pre-commit
----------------
- `pre-commit run --all-files` — run all hooks against the whole repo.
- Hooks run automatically on `git commit` after installation.

CI integration
--------------
We recommend adding a CI job that runs `pre-commit run --all-files` (or `detect-secrets` scan) to block secrets in pull requests. The CI job should fail if new secrets are detected.

Baseline maintenance
--------------------
If hooks flag known, intentional false positives (e.g., test fixtures), add them to `.secrets.baseline` using `detect-secrets audit` and commit the baseline.
