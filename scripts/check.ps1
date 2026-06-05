$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
}

Write-Host "Installing backend dependencies..."
& $venvPython -m pip install -e (Join-Path $root "backend[dev]")
if ($LASTEXITCODE -ne 0) { throw "Failed to install backend dependencies." }

Write-Host "Running backend tests..."
& (Join-Path $root ".venv\Scripts\pytest.exe") (Join-Path $root "backend")
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }

Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $root "frontend")
try {
    & $npm install
    if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies." }

    Write-Host "Building frontend..."
    & $npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
}
finally {
    Pop-Location
}

Write-Host "All checks passed."
