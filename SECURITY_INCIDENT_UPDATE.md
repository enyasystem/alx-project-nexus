Security Incident Update - detected hardcoded test secret

Summary
-------
- Date discovered: 2025-09-26
- Detected by: GitGuardian on PR #10
- Detected secret: literal password `[REDACTED]`
- Where found: `accounts/tests.py` in commit `4a8da053a535b4cbe941010a5cb6da6e1c8c7892` (short: `4a8da05`)
- GitGuardian finding id: 20808320

Immediate remediation (recommended)
----------------------------------
1) Treat the credential as compromised and rotate or revoke it immediately in any service where it may have been used.
   - If this was only a local test password and not used externally, mark as rotated for audit.
2) Update any CI secrets (GitHub Actions) or environment variables that could rely on the rotated credential.
3) Decide on history purge: rotate-only is acceptable for low-risk/test-only secrets; purge history for high-value secrets.

Quick purge plan (if you decide to remove secret from history)
-------------------------------------------------------------
- Backup current repo and push a backup branch/tag.
- Use `git-filter-repo` (recommended) to replace/remove the literal across all history.
- Test the cleaned mirror locally.
- Force-push `--all` and `--tags` to origin during a maintenance window and notify contributors to rebase or reclone.

Example commands (preview only — modify before running):

```powershell
# Locally create a time-stamped backup branch
git checkout -b backup/pre-purge-$(Get-Date -Format yyyyMMddHHmmss)
git push origin HEAD:refs/heads/backup/pre-purge-$(Get-Date -Format yyyyMMddHHmmss)

# Create a list file containing the secret(s) to remove
"[REDACTED]" | Out-File -Encoding utf8 ..\secrets-to-remove.txt

# On a separate clone (mirror) run (examples in bash):
# pip install git-filter-repo
# git clone --mirror https://github.com/enyasystem/alx-project-nexus.git
# cd alx-project-nexus.git
# git filter-repo --replace-text ../secrets-to-remove.txt
# git push --force --all
# git push --force --tags
```

Notification template
---------------------
Subject: [SECURITY] Credential rotation required — secret exposed in git history

Body:

```
Team,

GitGuardian detected a hardcoded secret `[REDACTED]` in commit 4a8da05 (file accounts/tests.py). Treat this credential as compromised. Please rotate/revoke it now and confirm here.

If we need to purge history, we'll schedule a maintenance window and I will perform the rewrite and force-push; contributors will need to rebase or reclone.

Thanks.
```

Next steps I can take for you
----------------------------
- Prepare an exact `git-filter-repo` command set and run it locally (preview), showing the before/after diff. I will not force-push without your confirmation.
- Create a small PR that adds a pre-commit secret check if you'd like to prevent recurrence.
- Add an incident entry to the repo's `SECURITY_INCIDENT.md` (if you want this file replaced rather than creating an update file).

Tell me which of the above you'd like me to do next.

Remediation record (actions performed)
-------------------------------------
The following actions were performed to remediate the detected hardcoded secret without destructively rewriting the contributor's branch.

- Created a fresh mirror clone and ran git-filter-repo to remove/replace the literal across history:

```powershell
# From local repo root
mkdir .\repo-mirror2.git
git clone --mirror --no-local . .\repo-mirror2.git
Set-Content -Path .\secrets-to-remove.txt -Value "test-pass-1==>[REDACTED]"
Set-Location -Path .\repo-mirror2.git
python -m git_filter_repo --replace-text ..\secrets-to-remove.txt --force
```

- Created a working clone from the cleaned mirror, created a timestamped cleaned branch, and pushed it to origin:

```powershell
Set-Location -Path ..
git clone .\repo-mirror2.git .\repo-cleaned2
Set-Location -Path .\repo-cleaned2
git checkout -b chore/add-precommit-hooks-clean-<TIMESTAMP>
git remote add github https://github.com/enyasystem/alx-project-nexus.git
git push github chore/add-precommit-hooks-clean-<TIMESTAMP>:chore/add-precommit-hooks-clean-<TIMESTAMP>
```

- Opened a PR from the cleaned branch and, after verifying GitGuardian and CI checks passed, merged the sanitized PR into `main`.

   - Sanitized PR: https://github.com/enyasystem/alx-project-nexus/pull/12
   - Merge commit: c963671583f1 (merged by @enyasystem)

- I left a comment on the original PR (#10) explaining the remediation and linking to the sanitized PR and incident doc.

Notes
-----
- This approach avoids force-pushing the contributor's branch. If you prefer to rewrite the original branch in place (force-push), I can prepare the full `git-filter-repo` commands and coordinate a maintenance window.
- Even after history cleanup you must rotate/revoke the exposed credential if it was used anywhere.

Publish workflow (OpenAPI) remediation
-------------------------------------
I inspected the failing OpenAPI publish workflow run (previous run id: 18044170813). The failure is consistent with a push/permission error when the workflow attempted to push built docs to the `gh-pages` branch.

What I changed
- Updated `.github/workflows/publish-openapi.yml` to detect whether a `PAGES_PAT` repo secret is present and to prefer it; otherwise the workflow falls back to using `GITHUB_TOKEN`.
- The workflow now uses a `detect-token` step and selects the appropriate deploy step via step outputs to avoid runtime conditional pitfalls.

Recommended final steps
- Option A (recommended): Create a repository secret named `PAGES_PAT` containing a personal access token with the following scopes: `repo` and `workflow` (for private repos use `repo` scope; for public-only repos `public_repo` may be sufficient). Then re-run the publish workflow — it should be able to push and succeed.
- Option B: If you prefer using `GITHUB_TOKEN` only, ensure repository settings allow GitHub Actions to write repository contents (Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests / read and write permissions). After that re-run the workflow.

I can create a follow-up PR that tweaks the workflow further (for example add debugging output or a single-step deploy) if you want me to.
\n
