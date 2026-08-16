@echo off
setlocal
cd /d "%~dp0"

REM ─────────────────────────────────────────────
REM NexuX V7.0 — Windows Launcher
REM ─────────────────────────────────────────────

if not exist "backend\venv\Scripts\python.exe" (
  echo [NexuX] Python venv not found. Creating one now...
  python -m venv backend\venv
  if errorlevel 1 (
    echo [NexuX] Failed to create venv. Make sure Python 3.11+ is installed.
    pause
    exit /b 1
  )
)

set PY=backend\venv\Scripts\python.exe

echo [NexuX] Checking dependencies...
%PY% -c "import fastapi, faster_whisper, cv2" >nul 2>&1
if errorlevel 1 (
  echo [NexuX] Installing dependencies...
  %PY% -m pip install -r backend\requirements.txt
  if errorlevel 1 (
    echo [NexuX] Failed to install dependencies.
    pause
    exit /b 1
  )
)

echo [NexuX] Starting V7.0 backend on http://127.0.0.1:8000
cd backend
%PY% main.py
endlocal
