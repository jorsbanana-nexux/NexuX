from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "duration": "duration_seconds",
    "width": "width",
    "height": "height",
    "fps": "fps",
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def probe(path: Path) -> dict[str, Any]:
    result = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or f"ffprobe failed: {path}")
    payload = json.loads(result.stdout)
    video = next((s for s in payload.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise RuntimeError(f"No video stream: {path}")
    fps_num, fps_den = (video.get("r_frame_rate") or "0/1").split("/", 1)
    fps = float(fps_num) / max(float(fps_den), 1.0)
    return {
        "duration_seconds": float(payload.get("format", {}).get("duration") or 0.0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": fps,
        "frames": int(video.get("nb_frames") or 0) if str(video.get("nb_frames", "")).isdigit() else None,
    }


def frame_hash(path: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "framemd5", "-an", str(output)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or f"framemd5 failed: {path}")


def black_frame_scan(path: Path) -> dict[str, Any]:
    result = run([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-vf", "blackdetect=d=0.25:pix_th=0.98", "-an", "-f", "null", "-",
    ])
    hits = [line for line in result.stderr.splitlines() if "black_start:" in line]
    return {"black_segments": len(hits), "passed": len(hits) == 0}


def qa_one(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    meta = probe(path)
    errors: list[str] = []
    if expected.get("width") and meta["width"] != int(expected["width"]):
        errors.append(f"width {meta['width']} != {expected['width']}")
    if expected.get("height") and meta["height"] != int(expected["height"]):
        errors.append(f"height {meta['height']} != {expected['height']}")
    min_duration = float(expected.get("min_duration", 0.1))
    max_duration = expected.get("max_duration")
    if meta["duration_seconds"] < min_duration:
        errors.append(f"duration {meta['duration_seconds']:.3f} < {min_duration}")
    if max_duration is not None and meta["duration_seconds"] > float(max_duration):
        errors.append(f"duration {meta['duration_seconds']:.3f} > {max_duration}")
    black = black_frame_scan(path)
    return {"file": str(path), "meta": meta, "black_frame_qa": black, "passed": not errors and black["passed"], "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic metadata + frame-level QA for 10+ NexuX outputs.")
    parser.add_argument("manifest", type=Path, help="JSON manifest containing at least 10 output paths.")
    parser.add_argument("--report", type=Path, default=Path("benchmark_report.json"))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    cases = manifest.get("cases", [])
    if len(cases) < 10:
        raise SystemExit(f"Benchmark requires >=10 cases; got {len(cases)}")

    results: list[dict[str, Any]] = []
    for case in cases:
        output = Path(case["output"])
        results.append(qa_one(output, case.get("expected", {})))

    passed = sum(1 for item in results if item["passed"])
    report = {"total": len(results), "passed": passed, "failed": len(results) - passed, "cases": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"total": len(results), "passed": passed, "failed": len(results) - passed, "report": str(args.report)}, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
