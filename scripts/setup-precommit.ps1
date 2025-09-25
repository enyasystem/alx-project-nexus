<#
Set up pre-commit and detect-secrets for Windows PowerShell.

Run from repo root:
  ./scripts/setup-precommit.ps1
#>

Write-Host "Installing pre-commit and detect-secrets (pip)..."
python -m pip install --upgrade pip
python -m pip install pre-commit detect-secrets

Write-Host "Installing git hooks..."
pre-commit install

if (-not (Test-Path .secrets.baseline)) {
    Write-Host "Generating initial detect-secrets baseline (this may show potential secrets)"
    detect-secrets scan > .secrets.baseline
    Write-Host "Baseline created at .secrets.baseline. Review and commit this file." 
} else {
    Write-Host ".secrets.baseline already exists; skip baseline creation."
}

Write-Host "pre-commit setup complete."
