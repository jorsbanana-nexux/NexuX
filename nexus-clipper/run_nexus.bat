@echo off
cd /d "%~dp0"

REM ─────────────────────────────────────────────
REM NexuX V8.0 — Windows Launcher
REM ─────────────────────────────────────────────

set PY=backend\venv\Scripts\python.exe

if not exist "%PY%" (
    echo [NexuX] Python venv not found. Creating one now...
    python -m venv backend\venv
    set PY=backend\venv\Scripts\python.exe
    echo [NexuX] Installing dependencies...
    "%PY%" -m pip install -r backend\requirements.txt
)

REM Check critical dependencies
"%PY%" -c "import fastapi, yt_dlp" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [NexuX] Installing missing dependencies...
    "%PY%" -m pip install -r backend\requirements.txt
)

REM V8.0: System health check
echo [NexuX] V8.0 system health check...
"%PY%" -c "import sys; sys.path.insert(0, 'backend'); from engine.self_healer import check_system_health; h = check_system_health(); print(f'[NexuX] System: {\"OK\" if h[\"healthy\"] else \"ISSUES: \" + str(h[\"issues\"])}')" 2>nul

REM Start frontend
if exist frontend\node_modules (
    echo [NexuX] Starting frontend dev server...
    cd frontend && start /b npm run dev && cd ..
) else (
    echo [NexuX] Installing frontend dependencies...
    cd frontend && npm install && start /b npm run dev && cd ..
)

REM Start backend
echo [NexuX] Starting V8.0 backend on 127.0.0.1:8000...
cd backend
"%PY%" main.py
pause
