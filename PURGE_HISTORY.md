Purge Git History Plan

Goal

Remove sensitive secrets accidentally committed to this repository's history in a safe, auditable way and push the cleaned history to the remote. This plan uses git-filter-repo (recommended) on a local mirror to rewrite history, tests the rewritten repo, and then force-pushes to the remote. Everyone must reclone after the force-push.

Summary of steps

1. Prepare a local mirror of the repository.
2. Install and verify `git-filter-repo` is available.
3. Create a `purge-targets.txt` containing exact secret strings, filenames, or regex patterns that must be removed.
4. Run `git-filter-repo` over the mirror with a reversible backup.
5. Inspect the rewritten repo and run automated tests.
6. Coordinate with collaborators, then force-push the cleaned branches and tags.
7. Rotate secrets again and verify deployments.

When to use this

Only use this when secrets were definitely exposed publicly, or when legal/compliance requires removal. If you haven't confirmed public exposure, rotation + documentation is the safer first step.

Preconditions and warnings

- This is destructive to git history. It will change commit SHAs and requires everyone who has cloned the repo to reclone.
- Back up the repository (mirror + bundle) before proceeding.
- Ensure you have admin rights and a maintenance window.
- You'll still need to rotate credentials after a purge — removing from history doesn't guarantee no copies exist elsewhere.

Files added/changed by this procedure

- A new, cleaned mirror of the repository (local files only until you force-push).
- A backup archive of the original mirror (bundle or tar.gz).

Detailed commands (PowerShell)

1) Prepare a local mirror and backup (do this on a safe machine):

```powershell
# change to a workspace folder outside of the repo working copy
cd $env:USERPROFILE\Documents
# clone a bare mirror
git clone --mirror https://github.com/enyasystem/alx-project-nexus.git alx-project-nexus-mirror.git
cd alx-project-nexus-mirror.git
# create a backup bundle
git bundle create ../alx-project-nexus-backup.bundle --all
```

2) Install git-filter-repo

- On Linux/macOS: `pip install git-filter-repo`
- On Windows (recommended via Python): `py -3 -m pip install git-filter-repo`

Verify:

```powershell
py -3 -m git_filter_repo --version
```

3) Prepare `purge-targets.txt`

List exact strings and filenames that must be removed. Example entries (replace with your actual secrets):

- DJANGO_SECRET_KEY=REDACTED_SECRET_VALUE
- POSTGRES_PASSWORD=REDACTED_PASSWORD
- secret_file.txt

4) Run git-filter-repo (dry-run & actual)

First, a dry-run to see what would be removed and which commits are affected. (git-filter-repo doesn't have a built-in dry-run; instead we perform a reversible run by creating a backup branch):

```powershell
# create a safety branch pointing to refs/original/refs/heads/* to preserve originals (automatic with filter-repo)
# run filter-repo to replace strings and remove files
py -3 -m git_filter_repo --invert-paths --paths-from-file ../purge-targets.txt --refs refs/heads/* --replace-text ../purge-targets.txt
```

Note: `--replace-text` accepts a file formatted as documented in git-filter-repo docs. You can use `--invert-paths` to delete listed paths.

5) Inspect the rewritten mirror

```powershell
# inspect logs
git log --all --grep='DJANGO_SECRET_KEY' -n 20
# run tests (you may clone the rewritten mirror to a working directory)
cd ..
git clone alx-project-nexus-mirror.git alx-project-nexus-rewritten
cd alx-project-nexus-rewritten
# run the test suite in a safe environment
.
```

6) Force-push cleaned branches and tags (coordinate with team)

Only after review and approvals:

```powershell
cd ..\alx-project-nexus-mirror.git
# push all refs (force)
git push --force --all origin
git push --force --tags origin
```

7) Post-purge actions

- Notify all contributors to reclone: provide clear commands and a short window in which they should stop pushing to the repo.
- Rotate all credentials again just to be safe.
- Monitor systems for suspicious activity.

Rollback

If anything goes wrong, you can restore from the backup bundle:

```powershell
cd ..
git clone alx-project-nexus-backup.bundle restored.git
```

Contact/Support

If you want, I can prepare the exact `purge-targets.txt` and run the mirror steps locally and provide the commands to execute the final force-push. I will NOT force-push on your behalf unless you explicitly ask me to and provide the necessary credentials.
\n