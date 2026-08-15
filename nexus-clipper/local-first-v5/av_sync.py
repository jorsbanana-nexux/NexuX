from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _probe(path: Path, selector: str) -> list[dict[str, Any]]:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", selector,
        "-show_entries", "packet=pts_time,dts_time,duration_time",
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1200:] or "Unable to inspect media packets")
    try:
        return json.loads(result.stdout).get("packets", [])
    except json.JSONDecodeError as exc:
        raise RuntimeError("FFprobe packet output was invalid") from exc


def verify_av_sync(path: Path, tolerance: float = 0.050) -> dict[str, Any]:
    video = _probe(path, "v:0")
    audio = _probe(path, "a:0")
    if not video or not audio:
        return {"passed": False, "reason": "missing_stream_packets", "drift_seconds": None}
    def _bounds(packets: list[dict[str, Any]]) -> tuple[float, float]:
        starts = [float(p["pts_time"]) for p in packets if p.get("pts_time") is not None]
        ends = []
        for p in packets:
            if p.get("pts_time") is None:
                continue
            start = float(p["pts_time"])
            duration = float(p.get("duration_time") or 0.0)
            ends.append(start + max(0.0, duration))
        return (min(starts), max(ends))
    v_start, v_end = _bounds(video)
    a_start, a_end = _bounds(audio)
    drift = max(abs(v_start - a_start), abs(v_end - a_end))
    return {
        "passed": drift <= tolerance,
        "tolerance_seconds": tolerance,
        "video_start": round(v_start, 6),
        "audio_start": round(a_start, 6),
        "video_end": round(v_end, 6),
        "audio_end": round(a_end, 6),
        "drift_seconds": round(drift, 6),
    }
