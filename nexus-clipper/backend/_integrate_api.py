"""
NexuX V9.0 API Integration Loader
===================================
Loads all API addition files (V8.5 + V9.0) into the main FastAPI app.
This file is exec'd by main.py after the app and helpers are defined.

Each api_v*.py file uses @app.get/post decorators that register
endpoints on the FastAPI app instance.

Order matters: V8.5 additions first, then V9.0 additions.
"""

# ── V8.5 API Additions ──
API_ADDITION_FILES = [
    "api_v85_additions.py",          # Virality scores, caption quality
    "api_v85_hooks_reframe.py",       # Hook detection, auto-reframe
    "api_v85_autopost_analytics.py",  # Multi-platform autopost + analytics
    "api_v85_rerender.py",            # Personalization re-render
    # ── V9.0 API Additions ──
    "api_v90_overlays.py",            # Drag overlay burn-in
    "api_v85_repair.py",              # Self-repair diagnostics
    "api_v85_preview.py",             # Real-time FFmpeg preview
]

import os
import logging

log = logging.getLogger("nexus.api")

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_loaded = 0
_errors = []

for _fname in API_ADDITION_FILES:
    _fpath = os.path.join(_backend_dir, _fname)
    if not os.path.exists(_fpath):
        log.warning(f"[Integration] Skipping {_fname} — file not found")
        _errors.append(_fname)
        continue
    try:
        with open(_fpath, "r", encoding="utf-8") as _f:
            _code = _f.read()
        # Execute in the caller's namespace (main.py's globals)
        # This makes @app decorators register on the real app
        exec(compile(_code, _fpath, "exec"), globals())
        _loaded += 1
        log.info(f"[Integration] Loaded {_fname}")
    except Exception as _e:
        log.error(f"[Integration] Failed to load {_fname}: {_e}", exc_info=True)
        _errors.append(f"{_fname}: {_e}")

log.info(f"[Integration] {_loaded}/{len(API_ADDITION_FILES)} API additions loaded successfully")
if _errors:
    log.warning(f"[Integration] Errors: {_errors}")
