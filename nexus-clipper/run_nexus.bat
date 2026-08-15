@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\venv\Scripts\python.exe" (
  echo [NexuX] Python venv belum ada.
  echo [NexuX] Jalankan install_nexus.bat terlebih dahulu.
  pause
  exit /b 1
)

set PY=backend\venv\Scripts\python.exe

echo [NexuX] Checking canonical V5 dependencies...
%PY% -c "import fastapi, faster_whisper, cv2" >nul 2>&1
if errorlevel 1 (
  echo [NexuX] Installing Local-First V5 dependencies...
  %PY% -m pip install -r local-first-v5\requirements-local.txt
  if errorlevel 1 (
    echo [NexuX] Failed to install V5 dependencies.
    pause
    exit /b 1
  )
)

echo [NexuX] Starting canonical Local-First V5 API on http://127.0.0.1:8000
cd local-first-v5
..\backend\venv\Scripts\python.exe -m uvicorn canonical_api:app --host 127.0.0.1 --port 8000
endlocal
