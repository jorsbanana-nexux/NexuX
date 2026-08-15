# NexuX Local-First V5

Local-first clipping backend staged beside the legacy NexuX implementation. **V5 is URL-first and intentionally has no B-roll subsystem.**

## Pipeline

`YouTube URL -> local yt-dlp -> FFprobe -> faster-whisper -> content intelligence -> candidate ranking -> Smart EDL -> subject tracking -> virtual camera -> captions -> headline/emoji -> FFmpeg export`

## Run

```bash
cd nexus-clipper/local-first-v5
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-local.txt
uvicorn app:app --host 127.0.0.1 --port 8001
```

Swagger: `http://127.0.0.1:8001/docs`

## Primary workflow

`POST /youtube/preview` -> `POST /youtube/import` -> `POST /analyze/{job_id}` -> `POST /render/{job_id}` -> `GET /download/{job_id}`

Local file upload remains as a compatibility fallback at `POST /upload`.

## Rendering

The final compositor uses one canonical edit timeline for audio/video/subtitle mapping. Subject observations are remapped into output time before the virtual-camera path is built. The camera path is converted into time-varying FFmpeg crop expressions and then scaled to 1080x1920.

Caption presets:

- `karaoke`: grouped phrases + active-word highlight + pop scaling.
- `pop_line`: bold, high-contrast emphasis.
- `deep_diver`: restrained typography with keyword emphasis.

Headline is rendered in an upper safe-zone. Captions use a lower safe-zone and can move vertically from face observations. Emoji is optional and deterministic.

## Fonts

`POST /fonts` and `GET /fonts` manage `.ttf`, `.otf`, `.woff`, and `.woff2` assets. Invalid signatures are rejected and rendering can fall back to a system font.

## Quality gate

Local:

```bash
python quality_gate.py
python -m pytest -q
```

CI installs FFmpeg, the local dependency set, compiles every module, runs all deterministic tests, and runs the same quality gate.

The regression suite includes a **real synthetic-media FFmpeg render**. It generates a test source with video+audio, applies EDL concatenation, dynamic camera crop, ASS overlay, and verifies that the final MP4 is 1080x1920 with both audio and video streams.

## Benchmark

`benchmark.py` evaluates ranked candidates against reference clips using interval IoU and reports duration compliance, overlap rate, top-1 overlap, mean best overlap, and mean heuristic score.

Use a JSON file containing `candidates` and optional `reference_clips` to run it:

```bash
python benchmark.py benchmark_case.json
```

The benchmark is for engineering optimization. It does not claim prediction of any platform ranking algorithm and does not by itself prove commercial-platform superiority.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: local upload ceiling
- `MAX_VIDEO_DURATION_SECONDS`: maximum YouTube import duration
- `DOWNLOAD_TIMEOUT_SECONDS`: yt-dlp timeout

## Known production gate

A real user video plus downloaded Whisper model must still be executed on the target machine before this branch can be called production-ready. The repository currently contains deterministic code and synthetic-media render validation, but not a completed real-world benchmark corpus.
