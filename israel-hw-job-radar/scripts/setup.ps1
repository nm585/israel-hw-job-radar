$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
py -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host ""
Write-Host "Setup complete. Edit .env for Telegram, then run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python run.py --dry-run --no-seed -v"
