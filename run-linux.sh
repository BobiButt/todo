#!/usr/bin/env bash
# TaskFlow — one-click launcher for Linux / macOS
# Stops any existing services on ports 8000/5173, starts PostgreSQL,
# backend, frontend, and opens the app in your browser.

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

echo "================================================"
echo "  TaskFlow — starting PostgreSQL, backend, frontend"
echo "================================================"

# ----- 0. Stop any existing TaskFlow services -----
echo "[cleanup] stopping existing services on ports 8000 and 5173..."
if command -v lsof > /dev/null 2>&1; then
  lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
  lsof -ti:5173 | xargs -r kill -9 2>/dev/null || true
elif command -v fuser > /dev/null 2>&1; then
  fuser -k 8000/tcp 2>/dev/null || true
  fuser -k 5173/tcp 2>/dev/null || true
else
  echo "[cleanup] lsof/fuser not found — skipping port cleanup."
fi
sleep 1

# ----- 1. Start PostgreSQL -----
echo "[postgres] ensuring PostgreSQL is running..."
if command -v systemctl > /dev/null 2>&1; then
  sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null || true
elif command -v service > /dev/null 2>&1; then
  sudo service postgresql start 2>/dev/null || true
else
  echo "[postgres] systemctl/service not found — please start PostgreSQL manually."
fi
sleep 2

# ----- Backend -----
if [ ! -d "$BACKEND/.venv" ]; then
  echo "[backend] creating virtual environment..."
  python3 -m venv "$BACKEND/.venv"
fi

source "$BACKEND/.venv/bin/activate"

echo "[backend] installing dependencies..."
pip install -q -r "$BACKEND/requirements.txt"

if [ ! -f "$BACKEND/.env" ]; then
  echo "[backend] copying .env.example to .env (edit it with your AI keys!)..."
  cp -n "$BACKEND/.env.example" "$BACKEND/.env"
fi

echo "[backend] applying migrations..."
( cd "$BACKEND" && alembic upgrade head )

echo "[backend] seeding demo data..."
( cd "$BACKEND" && python seed.py )

echo "[backend] starting uvicorn on http://localhost:8000 ..."
( cd "$BACKEND" && uvicorn app.main:app --reload ) &
BACKEND_PID=$!

# ----- Frontend -----
echo "[frontend] installing npm dependencies..."
( cd "$FRONTEND" && npm install --silent )

echo "[frontend] starting Vite on http://localhost:5173 ..."
( cd "$FRONTEND" && npm run dev -- --port 5173 ) &
FRONTEND_PID=$!

# ----- Wait for servers, then open browser -----
echo "Waiting for servers to start..."
sleep 8

FRONTEND_URL="http://localhost:5173"

echo "Opening $FRONTEND_URL in your browser..."
if command -v xdg-open > /dev/null 2>&1; then
  xdg-open "$FRONTEND_URL" 2>/dev/null || true
elif command -v open > /dev/null 2>&1; then
  open "$FRONTEND_URL" 2>/dev/null || true
else
  echo "Could not detect a browser opener. Open $FRONTEND_URL manually."
fi

echo ""
echo "TaskFlow is running:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for user to interrupt, then clean up
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'; exit" INT TERM
wait
