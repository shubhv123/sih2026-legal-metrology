#!/bin/bash
echo "===================================================="
echo "Starting SIH26034 Legal Metrology Compliance Checker"
echo "===================================================="

# Determine Python binary
if [ -f "./env/bin/python" ]; then
    PYTHON_BIN="$(pwd)/env/bin/python"
elif [ -f "./backend/venv/bin/python" ]; then
    PYTHON_BIN="$(pwd)/backend/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "[1/2] Starting FastAPI Backend on http://localhost:8000 ..."
(cd backend && PYTHONPATH=. "$PYTHON_BIN" -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "[2/2] Starting React Frontend on http://localhost:5173 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Both servers running!"
echo "Frontend:         http://localhost:5173"
echo "Backend API Docs: http://localhost:8000/docs"
echo "Press Ctrl+C to terminate both servers."
echo "===================================================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
