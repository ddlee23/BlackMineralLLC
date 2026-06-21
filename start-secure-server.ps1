# Start the local HTTP server and open an ngrok HTTPS tunnel.
# Prerequisite: install ngrok and make sure it is on your PATH.
# Download from: https://ngrok.com/download

$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-Not (Test-Path $python)) {
    Write-Error "Python executable not found at '$python'. Activate your venv or update the path in this script."
    exit 1
}

$ngrok = 'ngrok'
try {
    $null = & $ngrok version 2>$null
} catch {
    Write-Error "ngrok is not installed or not on PATH. Install ngrok from https://ngrok.com/download and try again."
    exit 1
}

$port = 8000
Write-Host "Starting local server on http://localhost:$port" -ForegroundColor Cyan
Start-Process -NoNewWindow -FilePath $python -ArgumentList '-m', 'http.server', $port
Start-Sleep -Seconds 2
Write-Host "Starting ngrok tunnel to http://localhost:$port" -ForegroundColor Cyan
Start-Process -NoNewWindow -FilePath $ngrok -ArgumentList 'http', $port
Write-Host 'Once ngrok starts, copy the https:// URL from the ngrok console or web UI.' -ForegroundColor Yellow
