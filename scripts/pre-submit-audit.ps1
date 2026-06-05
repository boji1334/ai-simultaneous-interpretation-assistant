$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

Write-Output "== Pre-submit audit =="

$requiredFiles = @(
  "README.md",
  ".env.example",
  ".github/PULL_REQUEST_TEMPLATE.md",
  ".github/workflows/ci.yml",
  "backend/app/main.py",
  "backend/app/services/subtitle_state.py",
  "backend/app/services/audio_stream.py",
  "backend/app/services/provider_diagnostics.py",
  "frontend/src/main.tsx",
  "docs/competition-audit.md",
  "docs/submission-checklist.md",
  "assets/demo/demo-script.en.txt"
)

$missing = @()
foreach ($file in $requiredFiles) {
  if (-not (Test-Path -LiteralPath $file)) {
    $missing += $file
  }
}

if ($missing.Count -gt 0) {
  Write-Output "Missing required files:"
  $missing | ForEach-Object { Write-Output " - $_" }
  exit 1
}

Write-Output "Required files: OK"

$scanTargets = @("README.md", "backend", "frontend", "docs", "scripts", ".env.example", ".github", "assets")
$badText = rg -n --glob "!scripts/pre-submit-audit.ps1" "鑾|绗|鍚|寮犲|娉ㄦ|瀹炴|瀛楀|�|TODO|FIXME" @scanTargets 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Output "Text scan found suspicious content:"
  Write-Output $badText
  exit 1
}

Write-Output "Text scan: OK"

$listening = Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue |
  Where-Object { $_.State -eq "Listen" }
if ($listening) {
  Write-Output "Warning: development ports are still listening:"
  $listening | Format-Table -AutoSize | Out-String | Write-Output
} else {
  Write-Output "Development ports: OK"
}

$gitName = git config --get user.name
$gitEmail = git config --get user.email
$remotes = git remote -v
if (-not $gitName) {
  Write-Output "Warning: git user.name is not configured."
}
if (-not $gitEmail) {
  Write-Output "Warning: git user.email is not configured."
}
if (-not $remotes) {
  Write-Output "Warning: no git remote is configured."
}

Write-Output "Git status:"
git status --short

Write-Output ""
Write-Output "Recommended verification command:"
Write-Output ".\scripts\check.ps1"
