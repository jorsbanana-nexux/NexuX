"""
NexuX V9.7 — Persistent Settings Store
=======================================
Single JSON file backing the new Settings UI. Settings here take
priority over env vars — this fixes the classic bug where a user sets
WHISPER_MODEL=small but the engine keeps loading large-v3 anyway,
because the env var lives at import-time and the pipeline cached it.

File location: NEXUX_SETTINGS_PATH (default: engine/output/.nexux_settings.json)
"""
import os
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from engine.constants import OUTPUT_DIR

_lock = threading.Lock()

# The 3 curated WhisperX model variants exposed in the Settings UI.
MODEL_VARIANTS = {
    "small": {
        "label": "WhisperX small",
        "size_approx": "≈0.5 GB",
        "description": "Fastest, good for quick drafts on CPU",
    },
    "base": {
        "label": "WhisperX base",
        "size_approx": "≈0.3 GB",
        "description": "Balanced speed/quality for most clips",
    },
    "large-v3": {
        "label": "WhisperX large-v3",
        "size_approx": "≈3 GB",
        "description": "Maximum accuracy (GPU recommended)",
    },
}

DEFAULT_SETTINGS: Dict[str, Any] = {
    "transcription_model": "small",
    "language": None,            # None = auto-detect
    "diarization": False,        # HF_TOKEN-gated speaker identification
    "batch_size": 16,            # WhisperX batch size (higher = faster on GPU)
    "word_timestamps": True,     # karaoke alignment
    "proxy_url": "",             # overrides NEXUX_PROXY when set
    "player_clients": "",        # overrides NEXUX_PLAYER_CLIENTS when set
    "auto_update_ytdlp": True,   # feed the self-updater toggle
}

_settings: Dict[str, Any] = {}
_loaded = False
_path = Path(os.environ.get("NEXUX_SETTINGS_PATH", str(OUTPUT_DIR / ".nexux_settings.json")))


def _load() -> Dict[str, Any]:
    global _loaded
    with _lock:
        merged = dict(DEFAULT_SETTINGS)
        try:
            if _path.exists():
                disk = json.loads(_path.read_text())
                if isinstance(disk, dict):
                    merged.update({k: v for k, v in disk.items() if k in DEFAULT_SETTINGS})
        except Exception:
            # A corrupt settings file must never crash the app — defaults win.
            pass
        _settings.clear()
        _settings.update(merged)
        _loaded = True
        return dict(_settings)


def get(key: str, fallback: Optional[str] = None) -> Any:
    if not _loaded:
        _load()
    return _settings.get(key, fallback)


def all_settings() -> Dict[str, Any]:
    if not _loaded:
        _load()
    return dict(_settings)


def set_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Validate + persist a partial update. Unknown keys are rejected."""
    if not _loaded:
        _load()
    with _lock:
        for k, v in patch.items():
            if k not in DEFAULT_SETTINGS:
                raise KeyError(f"Unknown setting: {k}")
            if k == "transcription_model" and v not in MODEL_VARIANTS:
                raise ValueError(f"Unknown model variant: {v}")
            _settings[k] = v
        try:
            _path.parent.mkdir(parents=True, exist_ok=True)
            _write_tmp = _path.with_suffix(".tmp")
            _write_tmp.write_text(json.dumps(_settings, indent=2))
            _write_tmp.replace(_path)  # atomic rename — never a half-written file
        except Exception as e:
            raise IOError(f"Cannot persist settings: {e}")
    return dict(_settings)


def reset_loaded() -> None:
    """Test hook: force re-read from disk."""
    global _loaded
    _loaded = False
