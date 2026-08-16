from __future__ import annotations

import ast
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "app.py", "server.py", "canonical_api.py", "canonical_v6_pipeline.py", "analysis_bundle.py", "caption_runtime.py", "sequential_vision.py",
    "captions.py", "compositor.py", "editorial.py", "editorial_ranker.py", "editorial_intelligence.py", "boundary_optimizer.py", "audio_intelligence.py",
    "fonts.py", "scoring.py", "semantic_ranker.py", "timeline.py", "virtual_camera.py", "vision_quality.py",
    "youtube.py", "targeted_retrieval.py", "face_sampling.py", "transcription.py", "job_store.py", "process_supervisor.py", "av_sync.py",
    "streaming_vision.py", "stress_suite.py",
]
AGENT_ROOT = ROOT.parent / "backend" / "agents"


def compile_all() -> list[str]:
    failures: list[str] = []
    for name in REQUIRED:
        path = ROOT / name
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception as exc:
            failures.append(f"{name}: {exc}")
    return failures


def check_tools() -> list[str]:
    return [tool for tool in ("ffmpeg", "ffprobe", "yt-dlp") if shutil.which(tool) is None]


def check_imports() -> list[str]:
    modules = ("fastapi", "pydantic", "cv2", "numpy", "faster_whisper")
    return [module for module in modules if importlib.util.find_spec(module) is None]


def check_agent_integrity() -> list[str]:
    forbidden = {
        "agent_11_scene_segmenter.py": ("i*5", "range(12)"),
        "agent_12_subject_tracker.py": ('"center_x": 950', '"center_y": 500'),
        "agent_13_quality_checker.py": ('"score": 95', '"resolution": "1920x1080"'),
        "agent_21_quality_inspector.py": ('"passed":True', '"passed": True'),
        "agent_20_professional_editor.py": ("setpts=", "zoompan", "hflip", "eq=saturation="),
    }
    failures: list[str] = []
    for filename, needles in forbidden.items():
        path = AGENT_ROOT / filename
        if not path.exists():
            failures.append(f"Missing agent file: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in text:
                failures.append(f"Forbidden legacy pattern in {filename}: {needle}")
    return failures


def check_bundle_contract() -> list[str]:
    failures: list[str] = []
    bundle = ROOT / "analysis_bundle.py"
    app = ROOT / "app.py"
    server = ROOT / "server.py"
    canonical = ROOT / "canonical_api.py"
    v6_pipeline = ROOT / "canonical_v6_pipeline.py"
    if "SCHEMA_VERSION" not in bundle.read_text(encoding="utf-8"):
        failures.append("analysis_bundle.py has no schema version")
    app_text = app.read_text(encoding="utf-8")
    server_text = server.read_text(encoding="utf-8")
    canonical_text = canonical.read_text(encoding="utf-8")
    v6_text = v6_pipeline.read_text(encoding="utf-8")
    for needle in ("build_analysis_bundle", '"analysis_bundle": bundle.to_dict()'):
        if needle not in app_text:
            failures.append(f"Canonical app missing analysis bundle wiring: {needle}")
    for needle in ("build_analysis_bundle", "analysis_bundle=bundle.to_dict()"):
        if needle not in server_text:
            failures.append(f"Production server missing analysis bundle wiring: {needle}")
    for needle in ("run_v6_generation", "CORSMiddleware", "NEXUX_ALLOWED_ORIGINS"):
        if needle not in canonical_text:
            failures.append(f"Canonical API missing integration contract: {needle}")
    for needle in ("generate_candidates", "download_segment", "fetch_recon_audio", "caption-first-targeted"):
        if needle not in v6_text:
            failures.append(f"V6 pipeline missing integration contract: {needle}")
    if "persisted-analysis-bundle" not in canonical_text:
        failures.append("Canonical API does not reuse persisted analysis bundle")
    return failures


def check_no_broll_contract() -> list[str]:
    failures: list[str] = []
    for filename in ("app.py", "server.py", "canonical_api.py", "canonical_v6_pipeline.py", "analysis_bundle.py"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        if '"broll": False' not in text and "broll=False" not in text:
            failures.append(f"No-B-roll contract missing from {filename}")
    return failures


def main() -> int:
    syntax_failures = compile_all()
    missing_tools = check_tools()
    missing_imports = check_imports()
    agent_failures = check_agent_integrity()
    bundle_failures = check_bundle_contract()
    broll_failures = check_no_broll_contract()
    if syntax_failures:
        print("SYNTAX FAIL")
        print("\n".join(syntax_failures))
        return 1
    if missing_tools:
        print("MISSING MEDIA TOOLS:", ", ".join(missing_tools))
        return 2
    if missing_imports:
        print("MISSING PYTHON IMPORTS:", ", ".join(missing_imports))
        return 3
    if agent_failures:
        print("AGENT INTEGRITY FAIL")
        print("\n".join(agent_failures))
        return 4
    if bundle_failures:
        print("ANALYSIS BUNDLE CONTRACT FAIL")
        print("\n".join(bundle_failures))
        return 5
    if broll_failures:
        print("NO-BROLL CONTRACT FAIL")
        print("\n".join(broll_failures))
        return 6
    print("QUALITY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
