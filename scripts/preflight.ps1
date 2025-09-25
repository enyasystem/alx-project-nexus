<#
Preflight script

Checks for required secrets in a project .env file and optionally prints a masked
docker-compose config for debugging. Exits with non-zero codes on failure so CI
or local callers can fail fast.

Usage:
  ./scripts/preflight.ps1         # run local preflight checks
  ./scripts/preflight.ps1 -ShowCompose  # also print masked docker-compose config
#>

[CmdletBinding()]
param(
    [switch]$ShowCompose,
    [string]$EnvPath = "./.env"
)

function Read-DotEnv($path) {
    if (-not (Test-Path $path)) {
        Throw "Env file not found: $path"
    }
    Get-Content $path | Where-Object { $_ -and -not ($_ -match '^\s*#') } | ForEach-Object {
        $parts = $_ -split '=',2
        if ($parts.Count -ge 2) {
            [PSCustomObject]@{ Key = $parts[0].Trim(); Value = $parts[1].Trim() }
        }
    }
}

try {
    $envPathResolved = (Resolve-Path -LiteralPath $EnvPath).ProviderPath
} catch {
    Write-Error "Could not find env file at path: $EnvPath"
    exit 10
}

try {
    $entries = Read-DotEnv $envPathResolved
} catch {
    Write-Error $_.Exception.Message
    exit 11
}

$dbPass = $entries | Where-Object { $_.Key -eq 'POSTGRES_PASSWORD' -and $_.Value } | Select-Object -First 1
$djKey = $entries | Where-Object { $_.Key -eq 'DJANGO_SECRET_KEY' -and $_.Value } | Select-Object -First 1

if (-not $dbPass) {
    Write-Error "POSTGRES_PASSWORD is missing or empty in $envPathResolved"
    exit 2
}
if (-not $djKey) {
    Write-Error "DJANGO_SECRET_KEY is missing or empty in $envPathResolved"
    exit 3
}

Write-Host "Preflight OK: required secrets found in $envPathResolved"

if ($ShowCompose) {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        try {
            $compose = docker-compose config 2>$null | Out-String
            # mask the DB password if present in the output; use regex escape for the literal
            $masked = $compose -replace [Regex]::Escape($dbPass.Value), '****'
            Write-Host "--- docker-compose config (masked) ---"
            Write-Host $masked
            Write-Host "--- end compose ---"
        } catch {
            Write-Warning "docker-compose config failed or returned no output"
        }
    } else {
        Write-Warning "docker-compose not found in PATH; skipping compose print"
    }
}

exit 0
