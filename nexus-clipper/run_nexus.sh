#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY="backend/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[NexuX] Python venv belum ada. Jalankan installer/setup terlebih dahulu."
  exit 1
fi

"$PY" -c 'import fastapi, faster_whisper, cv2; print("V5 dependencies OK")'
cd local-first-v5
exec "../$PY" -m uvicorn server:app --host 0.0.0.0 --port 8000
