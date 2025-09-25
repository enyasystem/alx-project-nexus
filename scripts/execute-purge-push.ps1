<#
Execute the final force-push for a rewritten git mirror.

Usage (interactive):
    .\scripts\execute-purge-push.ps1

Usage (non-interactive):
    .\scripts\execute-purge-push.ps1 -MirrorDir 'C:\path\to\alx-project-nexus-mirror.git' -ConfirmPush

This script is intentionally conservative and requires typing the exact confirmation phrase before it will push.
It does NOT rotate secrets or perform any other remediation.

REQUIREMENTS:
- Run this from a safe admin machine during the maintenance window.
- Ensure backups (bundle) exist and team is notified.
- You must have network access and push permissions to origin.
#>

param(
    [string]$MirrorDir = "$env:USERPROFILE\Documents\alx-project-nexus-mirror.git",
    [string]$ExpectedRemote = 'origin',
    [switch]$ConfirmPush
)

function Fail([string]$msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

Write-Host "Mirror directory: $MirrorDir"

if (-not (Test-Path $MirrorDir)) { Fail "Mirror directory not found: $MirrorDir" }

Push-Location $MirrorDir

# Ensure this is a bare mirror (should contain HEAD or config)
if (-not (Test-Path (Join-Path $MirrorDir 'config'))) {
    Write-Host "Warning: mirror dir does not appear to be a bare mirror or lacks a git config file." -ForegroundColor Yellow
}

# Check remote
$remotes = git remote -v | Out-String
Write-Host "Remotes:\n$remotes"

if ($remotes -notmatch $ExpectedRemote) {
    Write-Host "Warning: expected remote name '$ExpectedRemote' not found in remotes." -ForegroundColor Yellow
    Write-Host "Proceeding only if you intentionally want to push to a different remote." -ForegroundColor Yellow
}

# Confirm presence of backup bundle
$bundleCandidate = Join-Path (Split-Path $MirrorDir -Parent) 'alx-project-nexus-backup.bundle'
if (-not (Test-Path $bundleCandidate)) {
    Write-Host "Backup bundle not found at $bundleCandidate" -ForegroundColor Yellow
    Write-Host "Proceed only if you have a backup elsewhere." -ForegroundColor Yellow
} else {
    Write-Host "Found backup bundle: $bundleCandidate" -ForegroundColor Green
}

# Final interactive confirmation unless -ConfirmPush supplied
$confirmPhrase = 'I UNDERSTAND AND AUTHORIZE THE FORCE PUSH'
if (-not $ConfirmPush) {
    Write-Host "IMPORTANT: This will force-push rewritten history to remote and will change commit SHAs for all branches." -ForegroundColor Yellow
    Write-Host "If you are ready, type the confirmation phrase exactly and press Enter:`n$confirmPhrase" -NoNewline
    $input = [Console]::In.ReadLine()
    if ($input -ne $confirmPhrase) { Fail "Confirmation phrase did not match. Aborting." }
} else {
    Write-Host "-ConfirmPush supplied; skipping interactive confirmation." -ForegroundColor Cyan
}

# Run the force-push commands and capture output
$timestamp = Get-Date -Format o
$logFile = Join-Path (Split-Path $MirrorDir -Parent) "purge_push_$($timestamp -replace '[:.]','-').log"
Write-Host "Logging push output to: $logFile"

# Push all branches
Write-Host "Pushing all branches (force) to $ExpectedRemote..."
$pushAllCmd = "git push --force --all $ExpectedRemote"
Write-Host "Running: $pushAllCmd"
$pushAll = & git push --force --all $ExpectedRemote 2>&1 | Tee-Object -FilePath $logFile -Append
if ($LASTEXITCODE -ne 0) {
    Write-Host "git push --force --all failed. See log: $logFile" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Push tags
Write-Host "Pushing tags (force) to $ExpectedRemote..."
$pushTagsCmd = "git push --force --tags $ExpectedRemote"
Write-Host "Running: $pushTagsCmd"
$pushTags = & git push --force --tags $ExpectedRemote 2>&1 | Tee-Object -FilePath $logFile -Append
if ($LASTEXITCODE -ne 0) {
    Write-Host "git push --force --tags failed. See log: $logFile" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Force-push completed successfully." -ForegroundColor Green
Write-Host "Next steps (must be done immediately):" -ForegroundColor Cyan
Write-Host "1) Rotate all affected credentials and update deployments." -NoNewline; Write-Host " (See SECURITY_INCIDENT.md)" -ForegroundColor Cyan
Write-Host "2) Send the final notification to contributors with reclone instructions (Purge_Notice_Final.md)." -ForegroundColor Cyan
Write-Host "3) Monitor CI and production for anomalies for 72 hours." -ForegroundColor Cyan
Write-Host "Push log saved to: $logFile" -ForegroundColor Green

Pop-Location
