"""
NexuX V8.0 — Legacy server.py Deprecation Shim
================================================
DEPRECATED: All server routes now live in backend/main.py.

This file previously mounted additional routes (file serving, background
tasks) onto the local-first-v5 FastAPI app. Since V8.0, backend/main.py
handles everything including static file serving.

If imported, it re-exports the canonical app for backward compatibility.
No additional routes are mounted.
"""
from __future__ import annotations

import logging

log = logging.getLogger("nexux.legacy.server")

# Re-export app from the deprecation shim
from app import app  # noqa: F401

log.info("server.py: DEPRECATED — re-exporting from app.py shim (which re-exports backend/main.py)")
