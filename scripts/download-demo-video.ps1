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

Invoke-WebRequest -Uri $Url -OutFile $outputPath

Write-Host "Download complete."
Write-Host "Attribution: MIT OpenCourseWare / MITx, via Wikimedia Commons."
Write-Host "License: Creative Commons Attribution-Share Alike 4.0."
