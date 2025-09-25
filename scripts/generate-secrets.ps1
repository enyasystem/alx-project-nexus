<#
Generate strong secrets for rotation and save them locally to a timestamped file.
Usage: Run locally on a secure machine. This script prints the generated values and writes them to a local file in your Documents folder (not committed).

It also prints suggested gh CLI commands (if you have a token with proper permissions) and a short note on updating GitHub Actions via the web UI.
#>

param(
    [string]$outputDir = "$env:USERPROFILE\Documents",
    [int]$djangoKeyLength = 50,
    [int]$postgresLength = 32
)

function New-RandomString($length) {
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $bytes = New-Object 'byte[]' ($length)
    $rng.GetBytes($bytes)
    # base64-url safe
    $s = [System.Convert]::ToBase64String($bytes)
    $s = $s -replace '\+', '-' -replace '/', '_' -replace '=', ''
    return $s.Substring(0, [Math]::Min($length, $s.Length))
}

$django = New-RandomString $djangoKeyLength
$pg = New-RandomString $postgresLength
$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$outFile = Join-Path $outputDir "rotation-$timestamp.env"

$envText = @()
$envText += "DJANGO_SECRET_KEY=$django"
$envText += "POSTGRES_PASSWORD=$pg"

# Write file with restrictive permissions
Set-Content -Path $outFile -Value $envText -NoNewline
# Attempt to set file attributes to Hidden (Windows)
try { (Get-Item $outFile).Attributes = 'Hidden' } catch { }

Write-Host "Generated secrets saved to: $outFile" -ForegroundColor Green
Write-Host "---"
Write-Host "DJANGO_SECRET_KEY: $django" -ForegroundColor Yellow
Write-Host "POSTGRES_PASSWORD: $pg" -ForegroundColor Yellow
Write-Host "---"

Write-Host "Suggested gh CLI commands (requires token with repo admin):" -ForegroundColor Cyan
Write-Host "gh secret set DJANGO_SECRET_KEY --body \"$django\" --repo enyasystem/alx-project-nexus" -ForegroundColor Gray
Write-Host "gh secret set POSTGRES_PASSWORD --body \"$pg\" --repo enyasystem/alx-project-nexus" -ForegroundColor Gray

Write-Host "If you don't have gh or lack permission, update the repository secrets in GitHub web UI: Settings -> Secrets and variables -> Actions -> New repository secret" -ForegroundColor Cyan

Write-Host "Security: Do NOT commit the generated file. Delete it after applying secrets to your CI and deployments." -ForegroundColor Red
