#!/bin/bash
set -e

echo "=== PitchSheet Agent ==="
echo ""

# Start backend
echo "[1/2] Starting backend on http://localhost:8000 ..."
cd backend
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3.11 -m venv venv 2>/dev/null || python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "[2/2] Starting frontend on http://localhost:3000 ..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install --silent
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "PitchSheet Agent is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
