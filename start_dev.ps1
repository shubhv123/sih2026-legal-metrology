Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Starting SIH26034 Legal Metrology Compliance Checker" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

Write-Host "[2/2] Starting React Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev"

Write-Host ""
Write-Host "Both servers started!" -ForegroundColor Yellow
Write-Host "Frontend:         http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan
