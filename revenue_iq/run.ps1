$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Ambiente .venv não encontrado. Consulte revenue_iq/README.md."
}

$api = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "revenue_iq.api.app:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

$site = Start-Process -FilePath $python `
    -ArgumentList "-m", "http.server", "8765", "--bind", "127.0.0.1" `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8765/revenue-ai-dashboard-mockup.html"

Write-Host "RevenueIQ iniciado."
Write-Host "Dashboard: http://127.0.0.1:8765/revenue-ai-dashboard-mockup.html"
Write-Host "API:       http://127.0.0.1:8000/docs"
Write-Host "Processos:  API=$($api.Id), Site=$($site.Id)"
