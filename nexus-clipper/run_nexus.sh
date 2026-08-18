#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ─────────────────────────────────────────────
# NexuX V8.0 — Launcher
# ─────────────────────────────────────────────

PY="backend/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[NexuX] Python venv not found. Creating one now..."
  python3 -m venv backend/venv
  PY="backend/venv/bin/python"
  echo "[NexuX] Installing dependencies..."
  "$PY" -m pip install -r backend/requirements.txt
fi

# Check critical dependencies
if ! "$PY" -c 'import fastapi, yt_dlp' >/dev/null 2>&1; then
  echo "[NexuX] Installing missing dependencies..."
  "$PY" -m pip install -r backend/requirements.txt
fi

# V8.0: Check system health before starting
echo "[NexuX] V8.0 system health check..."
"$PY" -c "
import sys; sys.path.insert(0, 'backend')
from engine.self_healer import check_system_health
h = check_system_health()
if h['healthy']:
    print(f'[NexuX] ✅ System healthy | Disk: {h.get(\"disk_free_gb\", \"?\")} GB free')
else:
    print(f'[NexuX] ⚠️  Issues: {h[\"issues\"]}')
" || true

# Start frontend dev server in background
if [[ -d frontend/node_modules ]]; then
  echo "[NexuX] Starting frontend dev server..."
  cd frontend && npm run dev &
  cd ..
else
  echo "[NexuX] Installing frontend dependencies..."
  cd frontend && npm install && npm run dev &
  cd ..
fi

# Start the V8.0 backend
echo "[NexuX] Starting V8.0 backend on 127.0.0.1:8000..."
cd backend
exec "$PY" main.py
