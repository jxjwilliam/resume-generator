#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Resume WebUI Launcher ==="

# Install Python deps if needed
cd "$REPO_ROOT"
pip install -q fastapi uvicorn aiosqlite sse-starlette pypdf 2>/dev/null || true

# Install frontend deps if needed
cd "$REPO_ROOT/ui/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# Start backend
echo "Starting backend on http://127.0.0.1:5301"
cd "$REPO_ROOT"
python -m uvicorn ui.backend.main:app --host 127.0.0.1 --port 5301 --reload &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:5300"
cd "$REPO_ROOT/ui/frontend"
npx vite --host &
FRONTEND_PID=$!

# Cleanup on exit
cleanup() {
  echo "Shutting down..."
  kill "$BACKEND_PID" 2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  wait
}
trap cleanup EXIT INT TERM

echo ""
echo "Open http://localhost:5300 in your browser"
echo "Press Ctrl+C to stop"
wait
