param(
    [string]$Url = "https://upload.wikimedia.org/wikipedia/commons/transcoded/a/a0/Welcome_%286.002x-1%29.webm/Welcome_%286.002x-1%29.webm.360p.vp9.webm",
    [string]$Output = "assets/demo/external-course-demo.webm"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$outputPath = Join-Path $root $Output
$outputDir = Split-Path -Parent $outputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Write-Host "Downloading public demo video..."
Write-Host "Source: $Url"
Write-Host "Output: $outputPath"

$userAgent = "ai-simultaneous-interpretation-assistant/0.1 (educational demo; repository: boji1334)"
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue

try {
    if ($curl) {
        & $curl.Source -L -A $userAgent --fail --output $outputPath $Url
        if ($LASTEXITCODE -ne 0) {
            throw "curl.exe exited with code $LASTEXITCODE"
        }
    } else {
        Invoke-WebRequest -Uri $Url -OutFile $outputPath -UserAgent $userAgent
    }
} catch {
    Write-Host "Download failed. If the source rate-limits anonymous traffic, retry later or pass a different licensed video URL with -Url."
    throw
}

Write-Host "Download complete."
Write-Host "Attribution: MIT OpenCourseWare / MITx, via Wikimedia Commons."
Write-Host "License: Creative Commons Attribution-Share Alike 4.0."
