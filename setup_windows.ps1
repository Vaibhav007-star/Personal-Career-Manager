# Personal Career Management System — Windows setup (Phase 1)
# Run from PowerShell. Execution policy: if blocked, use:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Resolve-Python {
    $candidates = @(
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )
    foreach ($item in $candidates) {
        if ($item -and (Test-Path $item) -and ($item -notlike "*\Launcher\py.exe")) { return $item }
    }
    return $null
}

$pythonExe = Resolve-Python
if (-not $pythonExe) {
    Write-Error "Python 3.12 was not found. Install it from python.org and tick 'Add python.exe to PATH', or use: py -3.12"
}

Write-Host "Using $pythonExe"
& $pythonExe --version

if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment .venv ..."
    & $pythonExe -m venv .venv
}

Write-Host "Activating .venv ..."
& .\.venv\Scripts\Activate.ps1

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Created .env from .env.example. Edit it locally; never commit it."
}

New-Item -ItemType Directory -Force -Path ".\data", ".\logs", ".\uploads", ".\backups", ".\exports" | Out-Null

Write-Host "Initializing SQLite database ..."
& .\.venv\Scripts\python.exe -m database.init_db

Write-Host ""
Write-Host "Optional fictional sample data (not real credentials): python -m database.seed"
Write-Host "Run tests: python -m pytest -q"
Write-Host "Start app (loopback only): python -m streamlit run app.py --server.address 127.0.0.1"
Write-Host "Then open http://127.0.0.1:8501 in your browser."
