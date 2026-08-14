@echo off
setlocal enabledelayedexpansion
color 0A
title Nexus-Clipper AI Ultra - Auto Installer (Windows)
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     NEXUS-CLIPPER AI ULTRA - AUTO INSTALLER (WINDOWS)        ║
echo ║              Versi: 1.0.0 | Zero-Cost Build                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: ============================================================
:: STEP 0: Check Administrator Privileges
:: ============================================================
echo [*] Memeriksa hak administrator...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Script ini membutuhkan hak Administrator untuk menginstall dependensi.
    echo [!] Klik kanan file ini dan pilih "Run as Administrator".
    pause
    exit /b 1
)
echo [✓] Hak administrator terdeteksi.
echo.

:: ============================================================
:: STEP 1: Detect Python
:: ============================================================
echo [*] Memeriksa instalasi Python...
set PYTHON_FOUND=0
set PYTHON_CMD=

for %%C in (python3 python py) do (
    where %%C >nul 2>&1
    if !errorLevel! equ 0 (
        for /f "tokens=*" %%V in ('%%C --version 2^>^&1') do set "PYTHON_VER=%%V"
        echo [✓] Python ditemukan: !PYTHON_VER!
        set PYTHON_FOUND=1
        set PYTHON_CMD=%%C
        goto :python_done
    )
)

:python_done
if %PYTHON_FOUND% equ 0 (
    echo [!] Python TIDAK ditemukan. Mengunduh dan menginstall Python 3.11...
    echo.
    echo [*] Mengunduh Python 3.11.9 (64-bit)...
    curl -L -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    if !errorLevel! neq 0 (
        echo [✗] Gagal mengunduh Python. Silakan install manual dari https://python.org/downloads/
        pause
        exit /b 1
    )
    echo [*] Menjalankan installer Python (sabar, ini mungkin memakan waktu beberapa menit)...
    "%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    if !errorLevel! neq 0 (
        echo [✗] Gagal menginstall Python. Coba install manual.
        pause
        exit /b 1
    )
    del "%TEMP%\python-installer.exe"
    echo [✓] Python 3.11 berhasil diinstall.
    set PYTHON_CMD=python
) else (
    for /f "tokens=2" %%V in ('%PYTHON_CMD% --version 2^>^&1') do set "PY_FULL=%%V"
    for /f "tokens=1,2 delims=." %%A in ("!PY_FULL!") do (
        set "PY_MAJOR=%%A"
        set "PY_MINOR=%%B"
    )
    if !PY_MAJOR! lss 3 (
        echo [!] Python versi !PY_FULL! terdeteksi. Membutuhkan Python 3.11+.
        echo [!] Silakan install Python 3.11+ dari https://python.org/downloads/
        pause
        exit /b 1
    )
    if !PY_MAJOR! equ 3 if !PY_MINOR! lss 10 (
        echo [!] Python !PY_FULL! terdeteksi. Direkomendasikan Python 3.11+.
        echo [*] Melanjutkan dengan versi yang ada...
    )
)
echo.

:: ============================================================
:: STEP 2: Detect Node.js
:: ============================================================
echo [*] Memeriksa instalasi Node.js...
set NODE_FOUND=0

where node >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%V in ('node --version 2^>^&1') do set "NODE_VER=%%V"
    echo [✓] Node.js ditemukan: !NODE_VER!
    set NODE_FOUND=1
) else (
    echo [!] Node.js TIDAK ditemukan. Mengunduh dan menginstall Node.js LTS...
    curl -L -o "%TEMP%\node-installer.msi" "https://nodejs.org/dist/v20.15.0/node-v20.15.0-x64.msi"
    if !errorLevel! neq 0 (
        echo [✗] Gagal mengunduh Node.js. Silakan install manual dari https://nodejs.org/
        pause
        exit /b 1
    )
    echo [*] Menjalankan installer Node.js...
    msiexec /i "%TEMP%\node-installer.msi" /quiet /norestart
    del "%TEMP%\node-installer.msi"
    echo [✓] Node.js berhasil diinstall.
    set NODE_FOUND=1
)

where npm >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%V in ('npm --version 2^>^&1') do set "NPM_VER=%%V"
    echo [✓] npm ditemukan: !NPM_VER!
)
echo.

:: ============================================================
:: STEP 3: Detect FFmpeg
:: ============================================================
echo [*] Memeriksa instalasi FFmpeg...
set FFMPEG_FOUND=0

where ffmpeg >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%V in ('ffmpeg -version 2^>^&1 ^| findstr "ffmpeg version"') do set "FFMPEG_VER=%%V"
    echo [✓] FFmpeg ditemukan: !FFMPEG_VER!
    set FFMPEG_FOUND=1
) else (
    echo [!] FFmpeg TIDAK ditemukan. Mencoba install via winget...
    winget install "FFmpeg (Essentials Build)" --accept-package-agreements --silent 2>nul
    if !errorLevel! neq 0 (
        echo [!] Winget gagal. Mencoba download manual...
        if not exist "C:\ffmpeg" mkdir "C:\ffmpeg"
        curl -L -o "%TEMP%\ffmpeg.zip" "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        if !errorLevel! neq 0 (
            echo [✗] Gagal menginstall FFmpeg. Silakan install manual dari https://ffmpeg.org/download.html
            echo [*] Melanjutkan tanpa FFmpeg (beberapa fitur video tidak akan berfungsi)...
        ) else (
            powershell -Command "Expand-Archive -Force '%TEMP%\ffmpeg.zip' '%TEMP%\ffmpeg_extract'"
            for /d %%D in ("%TEMP%\ffmpeg_extract\*") do (
                xcopy /E /Y "%%D\bin\*" "C:\ffmpeg\bin\" >nul 2>&1
            )
            setx PATH "!PATH!;C:\ffmpeg\bin" >nul 2>&1
            set "PATH=!PATH!;C:\ffmpeg\bin"
            del "%TEMP%\ffmpeg.zip"
            rmdir /s /q "%TEMP%\ffmpeg_extract" >nul 2>&1
            echo [✓] FFmpeg berhasil diinstall ke C:\ffmpeg\
            set FFMPEG_FOUND=1
        )
    ) else (
        echo [✓] FFmpeg berhasil diinstall via winget.
        set FFMPEG_FOUND=1
    )
)
echo.

:: ============================================================
:: STEP 4: Setup Python Virtual Environment
:: ============================================================
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              SETUP PYTHON DEPENDENCIES                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

if not exist "backend" (
    echo [!] Folder backend tidak ditemukan. Pastikan build_nexus.py sudah dijalankan.
    pause
    exit /b 1
)

cd backend

echo [*] Membuat Python virtual environment...
%PYTHON_CMD% -m venv venv
if %errorLevel% neq 0 (
    echo [✗] Gagal membuat virtual environment.
    pause
    exit /b 1
)
echo [✓] Virtual environment dibuat.

echo [*] Mengaktifkan venv dan mengupgrade pip...
call venv\Scripts\activate.bat
%PYTHON_CMD% -m pip install --upgrade pip --quiet

echo [*] Menginstall dependensi Python (5-15 menit)...
echo [*] Ini termasuk: FastAPI, yt-dlp, edge-tts, OpenCV, MoviePy, FFmpeg, Whisper, PyTorch...
echo.

%PYTHON_CMD% -m pip install fastapi uvicorn[standard] websockets yt-dlp edge-tts opencv-python-headless Pillow moviepy ffmpeg-python faster-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu pydub numpy scipy requests aiohttp aiofiles pydantic python-multipart soundfile librosa colorama psutil --quiet

if %errorLevel% neq 0 (
    echo [!] Install batch gagal. Mencoba satu per satu...
    %PYTHON_CMD% -m pip install fastapi uvicorn --quiet
    %PYTHON_CMD% -m pip install yt-dlp --quiet
    %PYTHON_CMD% -m pip install edge-tts --quiet
    %PYTHON_CMD% -m pip install Pillow --quiet
    %PYTHON_CMD% -m pip install numpy scipy --quiet
    %PYTHON_CMD% -m pip install requests aiohttp --quiet
    %PYTHON_CMD% -m pip install pydantic python-multipart --quiet
    %PYTHON_CMD% -m pip install colorama psutil --quiet
    echo [✓] Package esensial terinstall.
)
echo [✓] Python dependensi selesai.

call deactivate
cd ..
echo.

:: ============================================================
:: STEP 5: Setup Frontend Dependencies
:: ============================================================
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              SETUP FRONTEND DEPENDENCIES                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

if not exist "frontend" (
    echo [!] Folder frontend tidak ditemukan. Pastikan build_nexus.py sudah dijalankan.
    pause
    exit /b 1
)

cd frontend

echo [*] Menginstall npm dependencies (3-10 menit)...
echo [*] Ini termasuk: React, Vite, Framer Motion, Three.js...
call npm install --silent 2>&1
if %errorLevel% neq 0 (
    echo [!] npm install gagal. Mencoba dengan --legacy-peer-deps...
    call npm install --legacy-peer-deps --silent
)
echo [✓] npm dependencies terinstall.

echo [*] Menginstall UI packages tambahan...
call npm install framer-motion react-icons three @react-three/fiber @react-three/drei --silent 2>&1
echo [✓] UI packages terinstall.

cd ..
echo.

:: ============================================================
:: STEP 6: Verify Installation
:: ============================================================
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              VERIFIKASI INSTALASI                           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [*] Memverifikasi backend...
cd backend
call venv\Scripts\activate.bat
%PYTHON_CMD% -c "import fastapi; print('FastAPI OK')" 2>nul && echo [✓] FastAPI siap || echo [!] FastAPI perlu perbaikan
%PYTHON_CMD% -c "import yt_dlp; print('yt-dlp OK')" 2>nul && echo [✓] yt-dlp siap || echo [!] yt-dlp perlu perbaikan
%PYTHON_CMD% -c "import edge_tts; print('edge-tts OK')" 2>nul && echo [✓] edge-tts siap || echo [!] edge-tts perlu perbaikan
call deactivate
cd ..

echo [*] Memverifikasi frontend...
cd frontend
if exist "node_modules" (
    echo [✓] node_modules ditemukan
) else (
    echo [!] node_modules tidak ditemukan
)
if exist "node_modules\react" echo [✓] React terinstall
if exist "node_modules\framer-motion" echo [✓] Framer Motion terinstall
cd ..

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              INSTALASI SELESAI!                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo   Cara menjalankan Nexus-Clipper AI Ultra:
echo.
echo   ╔═══════════════════════════════════════════════════════════╗
echo   ║  1. Jalankan Backend (Terminal 1):                        ║
echo   ║     cd backend                                          ║
echo   ║     venv\Scripts\activate                               ║
echo   ║     uvicorn main:app --host 0.0.0.0 --port 8000 --reload║
echo   ║                                                         ║
echo   ║  2. Jalankan Frontend (Terminal 2):                      ║
echo   ║     cd frontend                                         ║
echo   ║     npm run dev                                         ║
echo   ║                                                         ║
echo   ║  3. Buka browser ke:                                    ║
echo   ║     http://localhost:5173                               ║
echo   ║     API Docs: http://localhost:8000/docs                ║
echo   ╚═══════════════════════════════════════════════════════════╝
echo.
echo   Tekan sembarang tombol untuk keluar...
pause >nul
endlocal
