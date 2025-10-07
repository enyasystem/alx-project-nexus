Purge Notice (Template)

Subject: Repository history rewrite — mandatory reclone

Hi team,

We've identified sensitive secrets in the repository history and will rewrite the repository history to remove them. This requires a force-push and a mandatory reclone for all contributors.

Planned window: [INSERT DATE/TIME]
Estimated downtime: No downtime for the app, but you must stop pushing until after the window and reclone afterward.

Steps for contributors (post-purge):

1) Rename your local worktrees (optional):

    git remote set-url origin https://github.com/enyasystem/alx-project-nexus.git

2) Remove your local copy and reclone (recommended):

    # Backup any local changes first
    git clone https://github.com/enyasystem/alx-project-nexus.git

3) Reapply local unmerged work: create patches, or rebase manually.

If you have any questions or need assistance, reply to this message or contact [owner/contact].

Thank you for your cooperation.
\n
