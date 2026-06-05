param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$venvUvicorn = Join-Path $root ".venv\Scripts\uvicorn.exe"
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
}

Write-Host "Installing backend dependencies..."
& $venvPython -m pip install -e (Join-Path $root "backend[dev]")
if ($LASTEXITCODE -ne 0) { throw "Failed to install backend dependencies." }

Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $root "frontend")
try {
    & $npm install
    if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies." }
}
finally {
    Pop-Location
}

Write-Host "Starting backend at http://${BackendHost}:${BackendPort}"
$backend = $null
$frontend = $null

try {
    $backend = Start-Process -FilePath $venvUvicorn -ArgumentList @(
        "backend.app.main:app",
        "--host", $BackendHost,
        "--port", "$BackendPort"
    ) -WorkingDirectory $root -PassThru -WindowStyle Hidden

Write-Host "Starting frontend at http://${FrontendHost}:${FrontendPort}"
    $env:VITE_API_BASE_URL = "http://${BackendHost}:${BackendPort}"
    $frontend = Start-Process -FilePath $npm -ArgumentList @(
        "run", "dev", "--",
        "--host", $FrontendHost,
        "--port", "$FrontendPort"
    ) -WorkingDirectory (Join-Path $root "frontend") -PassThru -WindowStyle Hidden
}
catch {
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force
    }
    if ($frontend -and -not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force
    }
    throw
}

Write-Host "Backend PID: $($backend.Id)"
Write-Host "Frontend PID: $($frontend.Id)"
Write-Host "Open http://${FrontendHost}:${FrontendPort}"
Write-Host "Stop with: .\scripts\stop-dev.ps1"
