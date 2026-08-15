#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY="backend/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[NexuX] Python venv belum ada. Jalankan installer/setup terlebih dahulu."
  exit 1
fi

if ! "$PY" -c 'import fastapi, faster_whisper, cv2' >/dev/null 2>&1; then
  echo "[NexuX] Installing Local-First V5 dependencies..."
  "$PY" -m pip install -r local-first-v5/requirements-local.txt
fi

cd local-first-v5
exec "../$PY" -m uvicorn server:app --host 127.0.0.1 --port 8000
