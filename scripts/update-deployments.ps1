<#
Helper to update deployment files (example for docker-compose) and restart services.
This script is a template because deployments differ by environment. It shows a safe pattern for updating env files and restarting containers.

Usage: Customize the paths to your deployment environment and run on the host that manages deployments.
#>
param(
    [string]$composePath = "C:\deploy\project-nexus\docker-compose.yml",
    [string]$envFilePath = "C:\deploy\project-nexus\.env",
    [string]$newEnvFile = "$env:USERPROFILE\Documents\rotation-latest.env"
)

if (-not (Test-Path $newEnvFile)) { Write-Host "New env file not found: $newEnvFile" -ForegroundColor Red; exit 1 }

Write-Host "Backing up current env to $envFilePath.bak"
Copy-Item -Path $envFilePath -Destination "$envFilePath.bak" -Force

Write-Host "Applying new env contents"
Copy-Item -Path $newEnvFile -Destination $envFilePath -Force

Write-Host "Restarting docker-compose services"
Push-Location (Split-Path $composePath)
docker-compose down
docker-compose up -d --build
Pop-Location

Write-Host "Deploy update complete. Verify logs and connectivity." -ForegroundColor Green
