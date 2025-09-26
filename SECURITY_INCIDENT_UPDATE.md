Security Incident Update - detected hardcoded test secret

Summary
-------
- Date discovered: 2025-09-26
- Detected by: GitGuardian on PR #10
- Detected secret: literal password `test-pass-1`
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
"test-pass-1" | Out-File -Encoding utf8 ..\secrets-to-remove.txt

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

GitGuardian detected a hardcoded secret `test-pass-1` in commit 4a8da05 (file accounts/tests.py). Treat this credential as compromised. Please rotate/revoke it now and confirm here.

If we need to purge history, we'll schedule a maintenance window and I will perform the rewrite and force-push; contributors will need to rebase or reclone.

Thanks.
```

Next steps I can take for you
----------------------------
- Prepare an exact `git-filter-repo` command set and run it locally (preview), showing the before/after diff. I will not force-push without your confirmation.
- Create a small PR that adds a pre-commit secret check if you'd like to prevent recurrence.
- Add an incident entry to the repo's `SECURITY_INCIDENT.md` (if you want this file replaced rather than creating an update file).

Tell me which of the above you'd like me to do next.
