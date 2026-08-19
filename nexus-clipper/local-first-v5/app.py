"""
NexuX V8.0 — Legacy Deprecation Shim
=====================================
This file replaces the legacy local-first-v5 FastAPI app.

DEPRECATED: The local-first-v5 runtime is no longer a separate API surface.
All requests are now handled by backend/main.py (the V8.0 canonical backend).

This shim exists solely for backward compatibility:
  - If someone runs `python app.py` from local-first-v5/, they get a warning
    and a redirect to the canonical backend.
  - The app object is re-exported for any code that imports it, but it is
    NOT a functioning API — it just returns 410 Gone with upgrade instructions.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

log = logging.getLogger("nexux.legacy")

# ── Deprecation Warning ──
DEPRECATION_MSG = (
    "\n╔══════════════════════════════════════════════════════════════╗\n"
    "║  NexuX V8.0 — local-first-v5 is DEPRECATED                  ║\n"
    "║                                                            ║\n"
    "║  The canonical API is now backend/main.py                  ║\n"
    "║  Run: cd backend && python main.py                         ║\n"
    "║                                                            ║\n"
    "║  This shim exists only for backward compatibility.          ║\n"
    "╚══════════════════════════════════════════════════════════════╝\n"
)

# Try to re-export from canonical backend
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:
    from main import app  # noqa: F401 — re-export canonical app
    log.info("Legacy app.py: re-exporting canonical backend/main.py app")
except ImportError:
    # If backend not importable, create a stub FastAPI that returns 410
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="NexuX Local-First V5 (DEPRECATED)",
        version="5.0.0-deprecated",
    )

    @app.get("/{path:path}")
    async def deprecated_redirect(path: str):
        return JSONResponse(
            status_code=410,
            content={
                "error": "DEPRECATED",
                "message": "local-first-v5 API is no longer active. Use backend/main.py instead.",
                "canonical_entry": "cd backend && python main.py",
                "api_base": "http://127.0.0.1:8000",
            },
        )

    log.warning(DEPRECATION_MSG)

# Re-export paths for any code that references them
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parent
DATA = ROOT / "data"
JOBS = DATA / "jobs"
OUTPUTS = ROOT / "outputs"

if __name__ == "__main__":
    print(DEPRECATION_MSG)
    print("To start the canonical backend:")
    print("  cd ../backend && python main.py")
    sys.exit(1)
