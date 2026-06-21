# Start a local HTTP server for the PWA from this folder.
# Usage: Open PowerShell in this folder and run:
#   .\start-server.ps1

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-Not (Test-Path $python)) {
    Write-Error "Python executable not found at '$python'. Activate your venv or update the path in this script."
    exit 1
}

$port = 8000
Write-Host "Starting local server on http://localhost:$port" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop."
& $python -m http.server $port
