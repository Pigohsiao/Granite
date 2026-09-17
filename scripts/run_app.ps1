$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python virtual environment not found. Run py -3 -m venv .venv first."
}
$env:PYTHONPATH = Join-Path $projectRoot "src"
& $python -m pigo_notes.app
