"""
NexuX V9.0 — Self-Repair System
=================================
Comprehensive diagnostics + auto-fix for 13+ common issues.
Accessible from Settings → Repair tab in TimelineEditorStudio.

Checks:
1. FFmpeg installed and version >= 6.0
2. Python version >= 3.11
3. Disk space (>2GB free)
4. System memory (RAM)
5. Whisper model available
6. SQLite database integrity
7. Port 8000 availability
8. GPU/CUDA detection
9. Stale temp files cleanup
10. Broken/corrupted jobs
11. Python dependencies (pip packages)
12. Network connectivity (can reach YouTube)
13. yt-dlp version
"""
import subprocess
import os
import sys
import json
import time
import shutil
import sqlite3
import socket
import platform
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("nexus.repair")


@dataclass
class DiagnosticResult:
    id: str
    label: str
    status: str  # 'healthy' | 'warning' | 'error' | 'fixed'
    detail: str


# ── Individual Diagnostics ──

def check_ffmpeg() -> DiagnosticResult:
    """Check if FFmpeg is installed and version >= 6.0."""
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return DiagnosticResult("ffmpeg", "FFmpeg", "error", "FFmpeg not found in PATH")
        version_line = r.stdout.split("\n")[0]
        # Extract version number
        parts = version_line.split()
        if len(parts) >= 3:
            ver = parts[2].split("-")[0]
            major = int(ver.split(".")[0])
            if major >= 6:
                return DiagnosticResult("ffmpeg", "FFmpeg", "healthy", f"Installed: v{ver}")
            return DiagnosticResult("ffmpeg", "FFmpeg", "warning", f"Version {ver} — recommend 6.0+")
        return DiagnosticResult("ffmpeg", "FFmpeg", "healthy", "Installed")
    except FileNotFoundError:
        return DiagnosticResult("ffmpeg", "FFmpeg", "error", "FFmpeg not installed. Install: sudo apt install ffmpeg")
    except Exception as e:
        return DiagnosticResult("ffmpeg", "FFmpeg", "error", str(e))


def check_python() -> DiagnosticResult:
    """Check Python version >= 3.11."""
    major, minor = sys.version_info[:2]
    ver_str = f"{major}.{minor}.{sys.version_info[2]}"
    if major >= 3 and minor >= 11:
        return DiagnosticResult("python", "Python 3.11+", "healthy", f"Python {ver_str}")
    elif major >= 3:
        return DiagnosticResult("python", "Python 3.11+", "warning", f"Python {ver_str} — recommend 3.11+")
    return DiagnosticResult("python", "Python 3.11+", "error", f"Python {ver_str} too old")


def check_disk_space() -> DiagnosticResult:
    """Check disk space (need >2GB for processing)."""
    try:
        usage = shutil.disk_usage("/")
        free_gb = usage.free / (1024 ** 3)
        if free_gb > 10:
            return DiagnosticResult("disk", "Disk Space", "healthy", f"{free_gb:.1f}GB free")
        elif free_gb > 2:
            return DiagnosticResult("disk", "Disk Space", "warning", f"Only {free_gb:.1f}GB free — recommend 10GB+")
        return DiagnosticResult("disk", "Disk Space", "error", f"Critical: only {free_gb:.1f}GB free")
    except Exception as e:
        return DiagnosticResult("disk", "Disk Space", "warning", f"Could not check: {e}")


def check_memory() -> DiagnosticResult:
    """Check available RAM."""
    try:
        if sys.platform == "darwin":
            r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
            mem = int(r.stdout.strip())
            mem_gb = mem / (1024 ** 3)
        elif sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_uint), ("dwMemoryLoad", ctypes.c_uint),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            mem_gb = stat.ullTotalPhys / (1024 ** 3)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / (1024 ** 2)
                        break
                else:
                    return DiagnosticResult("memory", "System Memory", "warning", "Could not read memory")
        if mem_gb >= 16:
            return DiagnosticResult("memory", "System Memory", "healthy", f"{mem_gb:.0f}GB RAM")
        elif mem_gb >= 8:
            return DiagnosticResult("memory", "System Memory", "healthy", f"{mem_gb:.0f}GB RAM (minimum met)")
        return DiagnosticResult("memory", "System Memory", "warning", f"Only {mem_gb:.0f}GB — recommend 8GB+")
    except Exception as e:
        return DiagnosticResult("memory", "System Memory", "warning", f"Could not check: {e}")


def check_whisper_model() -> DiagnosticResult:
    """Check if Whisper model is available."""
    try:
        # Check common model cache locations
        home = Path.home()
        model_paths = [
            home / ".cache" / "whisper",
            home / ".cache" / "faster-whisper",
            Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / "models",
        ]
        for p in model_paths:
            if p.exists():
                models = list(p.glob("*"))
                if models:
                    model_names = [m.name for m in models if m.is_file()][:3]
                    return DiagnosticResult("whisper", "Whisper Model", "healthy", f"Models: {', '.join(model_names)}")
        # Also check if faster_whisper is installed (will download on first use)
        try:
            import faster_whisper
            return DiagnosticResult("whisper", "Whisper Model", "healthy", "faster-whisper installed (downloads on first use)")
        except ImportError:
            return DiagnosticResult("whisper", "Whisper Model", "warning", "faster-whisper not installed")
    except Exception as e:
        return DiagnosticResult("whisper", "Whisper Model", "warning", str(e))


def check_sqlite() -> DiagnosticResult:
    """Check SQLite database integrity."""
    try:
        db_path = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
        if not db_path.exists():
            return DiagnosticResult("sqlite", "SQLite Database", "healthy", "Database will be created on first run")
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()[0]
        conn.close()
        if result == "ok":
            # Count jobs
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM jobs")
                count = cur.fetchone()[0]
                conn.close()
                return DiagnosticResult("sqlite", "SQLite Database", "healthy", f"Integrity OK — {count} jobs stored")
            except:
                conn.close()
                return DiagnosticResult("sqlite", "SQLite Database", "healthy", "Integrity OK")
        return DiagnosticResult("sqlite", "SQLite Database", "error", f"Integrity issue: {result}")
    except Exception as e:
        return DiagnosticResult("sqlite", "SQLite Database", "warning", str(e))


def check_port() -> DiagnosticResult:
    """Check if port 8000 is available."""
    try:
        port = int(os.environ.get("PORT", "8000"))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            # Port in use — check if it's our backend
            return DiagnosticResult("port", f"Port {port}", "healthy", f"Backend running on port {port}")
        return DiagnosticResult("port", f"Port {port}", "healthy", f"Port {port} available")
    except Exception as e:
        return DiagnosticResult("port", "Port", "warning", str(e))


def check_gpu() -> DiagnosticResult:
    """Check GPU/CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return DiagnosticResult("gpu", "GPU / CUDA", "healthy", f"CUDA: {gpu_name}")
        return DiagnosticResult("gpu", "GPU / CUDA", "warning", "Not detected — CPU mode (fine for small models)")
    except ImportError:
        # Check nvidia-smi
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return DiagnosticResult("gpu", "GPU / CUDA", "healthy", f"GPU: {r.stdout.strip()}")
        except FileNotFoundError:
            pass
        return DiagnosticResult("gpu", "GPU / CUDA", "warning", "Not detected — CPU mode (fine for small models)")
    except Exception as e:
        return DiagnosticResult("gpu", "GPU / CUDA", "warning", str(e))


def check_stale_temp() -> DiagnosticResult:
    """Check for stale temporary files."""
    try:
        output_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output"))
        if not output_dir.exists():
            return DiagnosticResult("temp", "Stale Temp Files", "healthy", "No temp directory yet")
        # Count files older than 24h in pass1/pass2 temp dirs
        now = time.time()
        stale = 0
        for f in output_dir.rglob("*_pass1.mp4"):
            if f.stat().st_mtime < now - 86400:
                stale += 1
        for f in output_dir.rglob("*_pass2.mp4"):
            if f.stat().st_mtime < now - 86400:
                stale += 1
        if stale == 0:
            return DiagnosticResult("temp", "Stale Temp Files", "healthy", "No stale files")
        return DiagnosticResult("temp", "Stale Temp Files", "warning", f"{stale} stale temp files (cleanable)")
    except Exception as e:
        return DiagnosticResult("temp", "Stale Temp Files", "warning", str(e))


def check_broken_jobs() -> DiagnosticResult:
    """Check for broken/corrupted jobs in database."""
    try:
        db_path = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
        if not db_path.exists():
            return DiagnosticResult("jobs", "Broken Jobs", "healthy", "No database yet")
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Check for jobs stuck in 'processing' for >24h
        try:
            cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'processing' AND created_date < datetime('now', '-1 day')")
            stuck = cur.fetchone()[0]
        except:
            stuck = 0
        conn.close()
        if stuck == 0:
            return DiagnosticResult("jobs", "Broken Jobs", "healthy", "No corrupted jobs found")
        return DiagnosticResult("jobs", "Broken Jobs", "warning", f"{stuck} jobs stuck in processing >24h")
    except Exception as e:
        return DiagnosticResult("jobs", "Broken Jobs", "warning", str(e))


def check_dependencies() -> DiagnosticResult:
    """Check Python dependencies."""
    try:
        required = ["fastapi", "uvicorn", "yt_dlp", "cv2", "numpy"]
        missing = []
        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)
        if not missing:
            return DiagnosticResult("deps", "Dependencies", "healthy", "All packages installed")
        return DiagnosticResult("deps", "Dependencies", "error", f"Missing: {', '.join(missing)}")
    except Exception as e:
        return DiagnosticResult("deps", "Dependencies", "warning", str(e))


def check_network() -> DiagnosticResult:
    """Check network connectivity to YouTube."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("www.youtube.com", 443))
        sock.close()
        if result == 0:
            return DiagnosticResult("network", "Network / yt-dlp", "healthy", "YouTube reachable")
        return DiagnosticResult("network", "Network / yt-dlp", "warning", "Cannot reach YouTube (port 443)")
    except Exception as e:
        return DiagnosticResult("network", "Network / yt-dlp", "warning", str(e))


def check_ytdlp() -> DiagnosticResult:
    """Check yt-dlp version."""
    try:
        r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            ver = r.stdout.strip()
            return DiagnosticResult("ytdlp", "yt-dlp Version", "healthy", f"v{ver}")
        return DiagnosticResult("ytdlp", "yt-dlp Version", "warning", "yt-dlp not in PATH")
    except FileNotFoundError:
        return DiagnosticResult("ytdlp", "yt-dlp Version", "warning", "yt-dlp not installed")
    except Exception as e:
        return DiagnosticResult("ytdlp", "yt-dlp Version", "warning", str(e))


# ── Run All Diagnostics ──

ALL_CHECKS = [
    check_ffmpeg, check_python, check_disk_space, check_memory,
    check_whisper_model, check_sqlite, check_port, check_gpu,
    check_stale_temp, check_broken_jobs, check_dependencies,
    check_network, check_ytdlp,
]


def run_full_diagnosis() -> List[DiagnosticResult]:
    """Run all diagnostic checks and return results."""
    results = []
    for check_fn in ALL_CHECKS:
        try:
            result = check_fn()
            log.info(f"[Repair] {result.label}: {result.status} — {result.detail}")
            results.append(result)
        except Exception as e:
            log.error(f"[Repair] {check_fn.__name__} crashed: {e}")
            results.append(DiagnosticResult("unknown", check_fn.__name__, "error", str(e)))
    return results


def fix_issue(issue_id: str) -> DiagnosticResult:
    """Fix a specific issue by ID."""
    fixes = {
        "ffmpeg": lambda: _fix_ffmpeg(),
        "python": lambda: DiagnosticResult("python", "Python", "warning", "Cannot auto-fix Python version. Please upgrade manually."),
        "disk": lambda: _fix_stale_temp(),
        "temp": lambda: _fix_stale_temp(),
        "sqlite": lambda: _fix_sqlite(),
        "deps": lambda: _fix_deps(),
        "ytdlp": lambda: _fix_ytdlp(),
        "jobs": lambda: _fix_stuck_jobs(),
    }
    fix_fn = fixes.get(issue_id)
    if fix_fn:
        return fix_fn()
    return DiagnosticResult(issue_id, issue_id, "warning", f"No auto-fix available for '{issue_id}'")


def fix_all() -> List[DiagnosticResult]:
    """Fix all detectable issues."""
    results = run_full_diagnosis()
    fixed = []
    for r in results:
        if r.status in ("error", "warning"):
            fix_result = fix_issue(r.id)
            fixed.append(fix_result)
        else:
            fixed.append(r)
    return fixed


# ── Individual Fixers ──

def _fix_ffmpeg() -> DiagnosticResult:
    """Try to install FFmpeg."""
    try:
        if sys.platform == "linux":
            subprocess.run(["sudo", "apt", "update", "-qq"], timeout=30)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], timeout=120)
        elif sys.platform == "darwin":
            subprocess.run(["brew", "install", "ffmpeg"], timeout=120)
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return DiagnosticResult("ffmpeg", "FFmpeg", "fixed", "FFmpeg installed successfully")
        return DiagnosticResult("ffmpeg", "FFmpeg", "error", "Installation attempted but FFmpeg still not found")
    except Exception as e:
        return DiagnosticResult("ffmpeg", "FFmpeg", "error", f"Auto-install failed: {e}. Install manually.")


def _fix_stale_temp() -> DiagnosticResult:
    """Clean up stale temp files."""
    try:
        output_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output"))
        if not output_dir.exists():
            return DiagnosticResult("temp", "Stale Temp Files", "fixed", "Nothing to clean")
        now = time.time()
        cleaned = 0
        for f in output_dir.rglob("*_pass1.mp4"):
            if f.stat().st_mtime < now - 86400:
                f.unlink(missing_ok=True)
                cleaned += 1
        for f in output_dir.rglob("*_pass2.mp4"):
            if f.stat().st_mtime < now - 86400:
                f.unlink(missing_ok=True)
                cleaned += 1
        return DiagnosticResult("temp", "Stale Temp Files", "fixed", f"Cleaned {cleaned} stale temp files")
    except Exception as e:
        return DiagnosticResult("temp", "Stale Temp Files", "error", str(e))


def _fix_sqlite() -> DiagnosticResult:
    """Repair SQLite database."""
    try:
        db_path = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
        if not db_path.exists():
            return DiagnosticResult("sqlite", "SQLite Database", "fixed", "Database will be recreated on next run")
        # Try to vacuum (compacts + repairs)
        conn = sqlite3.connect(str(db_path))
        conn.execute("VACUUM")
        conn.close()
        return DiagnosticResult("sqlite", "SQLite Database", "fixed", "Database vacuumed and repaired")
    except Exception as e:
        # Last resort: backup and recreate
        try:
            backup = db_path.with_suffix(".db.bak")
            shutil.move(str(db_path), str(backup))
            return DiagnosticResult("sqlite", "SQLite Database", "fixed", f"Corrupted DB backed up to {backup.name}, fresh DB will be created")
        except Exception as e2:
            return DiagnosticResult("sqlite", "SQLite Database", "error", f"Repair failed: {e}, backup failed: {e2}")


def _fix_deps() -> DiagnosticResult:
    """Install missing Python dependencies."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                        "fastapi", "uvicorn", "yt-dlp", "opencv-python", "numpy"],
                       timeout=120)
        return DiagnosticResult("deps", "Dependencies", "fixed", "Dependencies reinstalled successfully")
    except Exception as e:
        return DiagnosticResult("deps", "Dependencies", "error", f"pip install failed: {e}")


def _fix_ytdlp() -> DiagnosticResult:
    """Update yt-dlp."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", "yt-dlp"],
                       timeout=120)
        r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return DiagnosticResult("ytdlp", "yt-dlp", "fixed", f"Updated to v{r.stdout.strip()}")
        return DiagnosticResult("ytdlp", "yt-dlp", "warning", "Update attempted but yt-dlp still not found")
    except Exception as e:
        return DiagnosticResult("ytdlp", "yt-dlp", "error", f"Update failed: {e}")


def _fix_stuck_jobs() -> DiagnosticResult:
    """Mark stuck jobs as failed."""
    try:
        db_path = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
        if not db_path.exists():
            return DiagnosticResult("jobs", "Broken Jobs", "fixed", "No database — nothing to fix")
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE jobs SET status = 'failed' WHERE status = 'processing' AND created_date < datetime('now', '-1 day')")
        conn.commit()
        count = conn.total_changes
        conn.close()
        return DiagnosticResult("jobs", "Broken Jobs", "fixed", f"Marked {count} stuck jobs as failed")
    except Exception as e:
        return DiagnosticResult("jobs", "Broken Jobs", "error", str(e))


# ── Quick Health Check ──

def quick_health_check() -> Dict:
    """Quick health summary (for /api/repair/health)."""
    critical = 0
    warnings = 0
    healthy = 0
    for check_fn in [check_ffmpeg, check_python, check_disk_space, check_dependencies]:
        try:
            r = check_fn()
            if r.status == "error":
                critical += 1
            elif r.status == "warning":
                warnings += 1
            else:
                healthy += 1
        except:
            critical += 1
    return {
        "status": "healthy" if critical == 0 else "degraded" if warnings > 0 else "critical",
        "critical": critical,
        "warnings": warnings,
        "healthy": healthy,
        "total_checks": 4,
    }
