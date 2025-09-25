<#
PowerShell helper to prepare a local mirror and run git-filter-repo safely.
Usage: Run from a directory where you want to create the mirror. This script will not force-push.
#>
param(
    [string]$remoteUrl = 'https://github.com/enyasystem/alx-project-nexus.git',
    [string]$mirrorDir = "$env:USERPROFILE\Documents\alx-project-nexus-mirror.git",
    [string]$backupBundle = "$env:USERPROFILE\Documents\alx-project-nexus-backup.bundle",
    [string]$purgeTargets = "$PSScriptRoot\..\purge-targets.txt"
)

Write-Host "Remote URL: $remoteUrl"
Write-Host "Mirror directory: $mirrorDir"
Write-Host "Backup bundle: $backupBundle"
Write-Host "Purge targets file: $purgeTargets"

# Create mirror
if (Test-Path $mirrorDir) {
    Write-Host "Mirror dir exists. Please remove or pick another path: $mirrorDir" -ForegroundColor Yellow
    exit 1
}

git clone --mirror $remoteUrl $mirrorDir
if ($LASTEXITCODE -ne 0) { Write-Error "git clone --mirror failed."; exit $LASTEXITCODE }

Set-Location $mirrorDir

# Create backup bundle
git bundle create $backupBundle --all
if ($LASTEXITCODE -ne 0) { Write-Error "git bundle create failed."; exit $LASTEXITCODE }

Write-Host "Bundle created at $backupBundle"

# Install git-filter-repo if missing (attempt)
try {
    py -3 -m git_filter_repo --version > $null 2>&1
} catch {
    Write-Host "git-filter-repo not found in Python. Attempting to install via pip..."
    py -3 -m pip install git-filter-repo
}

# Verify again
py -3 -m git_filter_repo --version
if ($LASTEXITCODE -ne 0) { Write-Error "git-filter-repo is not available. Install it and re-run."; exit 1 }

Write-Host "git-filter-repo available. Next step: edit purge-targets.txt and then run the filter command manually as documented in PURGE_HISTORY.md" -ForegroundColor Green

# Provide the recommended filter command (do not run automatically)
$absPurgeTargets = (Resolve-Path $purgeTargets).Path
Write-Host "Recommended (manual) filter command (copy & paste):`n"
Write-Host "py -3 -m git_filter_repo --replace-text $absPurgeTargets --invert-paths --paths-from-file $absPurgeTargets --refs refs/heads/*" -ForegroundColor Cyan

Write-Host "Note: Review PURGE_HISTORY.md for detailed steps and safety checks. This script does NOT run the actual rewrite or push." -ForegroundColor Yellow
