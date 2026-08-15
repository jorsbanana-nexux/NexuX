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

echo [NexuX] Verifying canonical V5 dependencies...
%PY% -c "import fastapi, faster_whisper, cv2; print('V5 dependencies OK')"
if errorlevel 1 (
  echo [NexuX] V5 dependencies belum lengkap.
  echo [NexuX] Jalankan:
  echo     %PY% -m pip install -r local-first-v5\requirements-local.txt
  pause
  exit /b 1
)

echo [NexuX] Starting canonical local-first V5 API on http://127.0.0.1:8000
cd local-first-v5
..ackend\venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8000
endlocal
