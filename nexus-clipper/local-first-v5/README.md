# NexuX Local-First V5

V5 is the canonical local-first video clipping engine. It is designed to run without paid AI APIs, paid media libraries, or automatic B-roll. **NexuX does not generate or fetch B-roll.**

## Production pipeline

`YouTube URL -> local yt-dlp -> FFprobe -> faster-whisper -> content intelligence -> candidate ranking -> Smart EDL -> subject/face tracking -> virtual camera -> captions -> headline/emoji -> FFmpeg export`

The same source-to-output timeline drives video cuts, audio cuts, subtitle timing, and camera timing so the rendered result stays synchronized. Silence, filler words, and immediate repetition can be removed by the canonical EDL. 

## Canonical API

Run:

```bash
cd nexus-clipper/local-first-v5
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-local.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

The canonical compatibility surface used by the React frontend is:

`POST /api/generate` -> `GET /api/job/{job_id}` -> `DELETE /api/job/{job_id}` (optional cancellation) -> output under `/output/`.

The generation worker performs YouTube validation/download, local transcription, semantic candidate ranking, Smart EDL construction, face-aware camera tracking, deterministic captions, and FFmpeg rendering. Jobs are persisted under `data/jobs` so a process restart does not erase completed job metadata.

The original explicit workflow remains available for inspection and advanced use:

`POST /youtube/preview` -> `POST /youtube/import` -> `POST /analyze/{job_id}` -> `POST /render/{job_id}` -> `GET /download/{job_id}`.

## Rendering

Supported output aspect ratios are `9:16`, `1:1`, `16:9`, `4:5`, `2:3`, and `21:9`. The compositor crops to the requested aspect ratio, follows tracked subjects when available, and scales to the requested output dimensions.

Caption presets:

- `karaoke`: grouped phrases + active-word highlight + pop scaling.
- `pop_line`: bold, high-contrast emphasis.
- `deep_diver`: restrained typography with keyword emphasis.

Headline is rendered in an upper safe-zone. Captions use a lower safe-zone and can move based on face observations. Emoji is optional and deterministic.

## Fonts

`POST /fonts` and `GET /fonts` manage local font assets. Invalid font signatures are rejected and rendering can fall back to a system font.

## Quality gate

```bash
python quality_gate.py
python -m pytest -q
```

CI compiles the V5 modules, installs FFmpeg, runs deterministic tests, and executes the quality gate. The regression suite includes a synthetic-media FFmpeg render with video+audio, EDL concatenation, dynamic camera crop, ASS subtitles, and final-stream verification.

## Benchmark

`benchmark.py` evaluates ranked candidates against reference clips using interval IoU and reports duration compliance, overlap rate, top-1 overlap, mean best overlap, and mean heuristic score. This is an engineering benchmark, not a claim about any social platform's proprietary ranking algorithm.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: local upload ceiling
- `MAX_VIDEO_DURATION_SECONDS`: maximum YouTube import duration
- `DOWNLOAD_TIMEOUT_SECONDS`: yt-dlp timeout

## Production gate

The remaining validation step is running a real user video plus a downloaded Whisper model on the target machine and expanding the benchmark corpus with human-rated references. Until that is completed, performance should be described as engineering readiness rather than commercial equivalence.
