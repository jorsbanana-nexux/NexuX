#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ─────────────────────────────────────────────
# NexuX V7.0 — Launcher
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
if ! "$PY" -c 'import fastapi, faster_whisper, cv2' >/dev/null 2>&1; then
  echo "[NexuX] Installing missing dependencies..."
  "$PY" -m pip install -r backend/requirements.txt
fi

# Start the V7.0 backend
echo "[NexuX] Starting V7.0 backend on 127.0.0.1:8000..."
cd backend
exec "$PY" main.py
