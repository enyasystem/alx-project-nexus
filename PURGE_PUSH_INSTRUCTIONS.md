Purge: Push-Ready Instructions (FINAL)

Overview

These instructions are the final, push-ready steps to rewrite the repository history using the cleaned mirror and force-push the rewritten history to origin. Only run these steps during the agreed maintenance window and after you've confirmed the rewritten mirror looks correct and tests pass.

Important preconditions

- Backups exist: `alx-project-nexus-backup.bundle` or equivalent must be stored offsite.
- All collaborators notified and instructed to stop pushing during the maintenance window.
- You have admin write access to the `origin` remote and network access to GitHub.
- You've tested the rewritten mirror locally and verified sensitive strings are removed.

Checklist (run before the push)

1. Verify the mirror and rewritten copy are present locally.
   - Mirror dir example: `C:\Users\HP PC\Documents\alx-project-nexus-mirror.git`
   - Rewritten clone example: `C:\Users\HP PC\Documents\alx-project-nexus-rewritten`

2. Inspect rewritten history for any remaining secrets:

```powershell
cd C:\Users\HP PC\Documents\alx-project-nexus-rewritten
# search for evidence of the secret substrings (use a short part of the secret)
git log --all --grep='PART_OF_SECRET' -n 50
# check for files with typical names
git rev-list --objects --all | grep -E "(\.env|secrets|credentials|secrets\.json)" || Write-Host "No suspicious filenames found"
```

3. Run the test suite in the rewritten repo and confirm it passes (or at least the smoke tests).

```powershell
# from the rewritten clone working dir
# optionally create a venv and install requirements
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py test --settings=project.settings_test
```

4. Final approvals obtained from stakeholders.

Push procedure (during window)

1) Switch to the mirror directory (this is the bare mirror created earlier):

```powershell
cd C:\Users\HP PC\Documents\alx-project-nexus-mirror.git
```

2) Ensure the origin remote is the correct remote (it should already be set):

```powershell
git remote -v
```

3) Force-push all branches and tags:

```powershell
# push all refs (branches)
git push --force --all origin
# push tags
git push --force --tags origin
```

4) Verify on GitHub web UI that branches and tags are updated and that PRs appear consistent (note: PRs will reference old commits — reviewers may need to rebase/close/reopen PRs).

Post-push steps

1. Rotate secrets again (must be done immediately after the force-push).
2. Send the final notification to collaborators with reclone instructions (see `Purge_Notice_Final.md`).
3. Require all contributors to reclone and rebase any in-progress work against the new history.
4. Monitor CI and production systems for 72 hours for anomalies.

Rollback plan

If anything goes wrong and you need to restore the original repo quickly:

```powershell
# create a local clone from the backup bundle
cd C:\Users\HP PC\Documents
git clone alx-project-nexus-backup.bundle restored.git
# push to origin (coordinate first) to restore
cd restored.git
git push --force --all origin
git push --force --tags origin
```

Support

If you want, I can perform a final run (no push) and produce a short diff report showing which commits and files changed or were removed. I will not perform the force-push for you unless explicitly asked and you provide confirmation and necessary access.
