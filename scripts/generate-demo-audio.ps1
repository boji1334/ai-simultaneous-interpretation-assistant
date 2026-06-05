param(
  [string]$InputPath = "assets/demo/demo-script.en.txt",
  [string]$OutputPath = "assets/demo/demo-en.wav",
  [int]$Rate = 0
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input script not found: $InputPath"
}

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutput = Join-Path (Resolve-Path -LiteralPath ".").Path $OutputPath
$outputDir = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Add-Type -AssemblyName System.Speech

$text = Get-Content -LiteralPath $resolvedInput -Raw -Encoding UTF8
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speaker.Rate = [Math]::Min([Math]::Max($Rate, -10), 10)
$speaker.SetOutputToWaveFile($resolvedOutput)
$speaker.Speak($text)
$speaker.Dispose()

Write-Output "Generated demo audio: $resolvedOutput"
