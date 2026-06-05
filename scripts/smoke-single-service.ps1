param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$venvUvicorn = Join-Path $root ".venv\Scripts\uvicorn.exe"
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$baseUrl = "http://${HostName}:${Port}"

if (-not (Test-Path -LiteralPath $venvPython)) {
  python -m venv (Join-Path $root ".venv")
  if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment." }
}

Write-Output "Installing backend dependencies..."
& $venvPython -m pip install -e (Join-Path $root "backend[dev]")
if ($LASTEXITCODE -ne 0) { throw "Failed to install backend dependencies." }

Write-Output "Building frontend for single-service mode..."
Push-Location (Join-Path $root "frontend")
try {
  & $npm install
  if ($LASTEXITCODE -ne 0) { throw "Failed to install frontend dependencies." }
  & $npm run build
  if ($LASTEXITCODE -ne 0) { throw "Failed to build frontend." }
}
finally {
  Pop-Location
}

$server = $null
try {
  Write-Output "Starting single-service app at $baseUrl"
  $server = Start-Process -FilePath $venvUvicorn -ArgumentList @(
    "backend.app.main:app",
    "--host", $HostName,
    "--port", "$Port"
  ) -WorkingDirectory $root -PassThru -WindowStyle Hidden

  & $venvPython (Join-Path $root "scripts\runtime_smoke.py") $baseUrl
  if ($LASTEXITCODE -ne 0) { throw "Runtime smoke checks failed." }
}
finally {
  if ($server -and -not $server.HasExited) {
    Stop-Process -Id $server.Id -Force
    Write-Output "Stopped single-service app."
  }
}
