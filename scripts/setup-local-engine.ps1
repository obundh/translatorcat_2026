$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$engineRoot = Join-Path $repoRoot ".translatorcat-engine"
$venvRoot = Join-Path $engineRoot ".venv"
$pythonExe = Join-Path $venvRoot "Scripts\python.exe"
$serverScript = Join-Path $repoRoot "scripts\local-translate-server.py"

New-Item -ItemType Directory -Force -Path $engineRoot | Out-Null

if (-not (Test-Path $pythonExe)) {
  python -m venv $venvRoot
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install argostranslate

& $pythonExe $serverScript --install en:ko ko:en

Write-Host ""
Write-Host "TranslatorCat local engine is ready."
Write-Host "Run: npm start"
