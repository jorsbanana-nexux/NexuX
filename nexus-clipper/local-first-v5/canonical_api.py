"""
NexuX V8.0 — Legacy canonical_api.py Deprecation Shim
======================================================
DEPRECATED: All canonical API endpoints now live in backend/main.py.

This file previously mounted the canonical API surface onto the local-first-v5
app. Since V8.0, backend/main.py is the single canonical API.

If imported, it re-exports the canonical app for backward compatibility.
No additional routes are mounted — they all come from main.py now.
"""
from __future__ import annotations

import logging

log = logging.getLogger("nexux.legacy.canonical_api")

# Re-export app from the deprecation shim
from app import app  # noqa: F401

log.info("canonical_api.py: DEPRECATED — re-exporting from app.py shim (which re-exports backend/main.py)")
