# FlowPilot one-command launcher (Windows PowerShell).
# Sets up the Python engine + web UI on first run, then starts the engine.
# Usage:  .\start.ps1            normal start
#         .\start.ps1 -Rebuild   force-rebuild the web UI first
param(
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

# 1) Python virtual environment
if (-not (Test-Path "$root\.venv\Scripts\python.exe")) {
    Write-Host "[1/4] Creating virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
}
$py = "$root\.venv\Scripts\python.exe"

# 2) Install the package + dependencies (only if missing)
& $py -c "import flowpilot.engine, fastapi, uvicorn, keyboard" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Cyan
    & $py -m pip install -e ".[dev]"
} else {
    Write-Host "[2/4] Python dependencies OK." -ForegroundColor DarkGray
}

# 3) Build the web UI if missing (or when -Rebuild is passed)
if ($Rebuild -and (Test-Path "$root\web\dist")) {
    Remove-Item "$root\web\dist" -Recurse -Force
}
if (-not (Test-Path "$root\web\dist\index.html")) {
    Write-Host "[3/4] Building the web UI (first run is slow)..." -ForegroundColor Cyan
    Push-Location "$root\web"
    if (-not (Test-Path "node_modules")) { npm install }
    npm run build
    Pop-Location
} else {
    Write-Host "[3/4] Web UI already built." -ForegroundColor DarkGray
}

# 4) Start the engine (serves the UI + API, opens the browser at http://127.0.0.1:8765)
Write-Host "[4/4] Starting FlowPilot at http://127.0.0.1:8765  (Ctrl+C to stop)" -ForegroundColor Green
& $py -m flowpilot.engine
