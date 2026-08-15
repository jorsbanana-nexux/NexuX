from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def make_fixture(path: Path, duration_seconds: int, *, width: int = 640, height: int = 360) -> None:
    result = _run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate=24",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", str(duration_seconds), "-shortest", "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path),
    ], timeout=max(300, duration_seconds * 4))
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3000:] or "Unable to create stress fixture")


def probe(path: Path) -> dict:
    result = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "ffprobe failed")
    return json.loads(result.stdout)


def run_preflight(duration_seconds: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="nexus-stress-") as tmp:
        root = Path(tmp)
        fixture = root / "fixture.mp4"
        started = time.perf_counter()
        make_fixture(fixture, duration_seconds)
        generation_seconds = time.perf_counter() - started
        meta = probe(fixture)
        return {
            "duration_seconds": duration_seconds,
            "fixture_bytes": fixture.stat().st_size,
            "fixture_generation_seconds": round(generation_seconds, 3),
            "video": {"width": meta["streams"][0].get("width"), "height": meta["streams"][0].get("height")},
            "audio_present": any(s.get("codec_type") == "audio" for s in meta.get("streams", [])),
        }


def run_failure_injection() -> dict[str, str]:
    return {
        "missing_source": "must produce a typed media-not-found failure without leaving a completed job",
        "corrupt_source": "must reject before transcription/render",
        "cancel_during_download": "must terminate download process and persist cancelled state",
        "cancel_during_transcription": "must terminate isolated Whisper worker and persist cancelled state",
        "cancel_during_render": "must terminate FFmpeg process and persist cancelled state",
        "restart_during_processing": "must recover stale processing jobs on startup",
        "render_av_drift": "must fail QA when packet timestamp drift exceeds tolerance",
        "missing_font": "must fall back deterministically without corrupting subtitle render",
        "disk_full": "must fail job cleanly and retain actionable error metadata",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="NexuX long-form stress preflight and failure-injection plan")
    parser.add_argument("--duration-minutes", type=int, nargs="+", default=[5, 30])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    reports = []
    for minutes in args.duration_minutes:
        if minutes <= 0:
            raise SystemExit("duration must be positive")
        reports.append(run_preflight(minutes * 60))
    payload = {"preflight": reports, "failure_injection": run_failure_injection(), "whisper_worker": os.getenv("NEXUS_TRANSCRIPTION_WORKER", "0")}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
