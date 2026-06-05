param(
    [int[]]$Ports = @(8000, 5173)
)

$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalPort $Ports -ErrorAction SilentlyContinue |
    Where-Object { $_.OwningProcess -and $_.OwningProcess -ne 0 } |
    Select-Object -ExpandProperty OwningProcess -Unique

if (-not $connections) {
    Write-Host "No development server processes found."
    exit 0
}

foreach ($processId in $connections) {
    Write-Host "Stopping process $processId"
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

Write-Host "Development servers stopped."

