@echo off
echo ====================================================
echo Starting SIH26034 Legal Metrology Compliance Checker
echo ====================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "FastAPI Backend" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting React Frontend on http://localhost:5173 ...
start "React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers started!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://localhost:8000/docs
echo ====================================================
