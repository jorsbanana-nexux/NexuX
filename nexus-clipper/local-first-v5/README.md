# NexuX Local-First V5

Local-first clipping backend staged beside the legacy NexuX implementation.

## Pipeline

`YouTube URL -> local yt-dlp -> FFprobe -> faster-whisper -> heuristic content analysis -> candidate ranking -> Smart EDL -> subject-aware camera path -> advanced ASS captions -> visual intelligence -> FFmpeg export`

## Run

```bash
cd nexus-clipper/local-first-v5
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-local.txt
uvicorn app:app --host 127.0.0.1 --port 8001
```

Swagger: `http://127.0.0.1:8001/docs`

## Caption presets

- `karaoke`: phrase grouping, active-word highlight and subtle pop scaling.
- `pop_line`: bold, high-contrast emphasis for fast content.
- `deep_diver`: restrained presentation with keyword emphasis.

Captions consume the canonical edited timeline when available, so removed source ranges do not independently shift subtitle timing.

## Visual intelligence

`visual_intel.py` is local and deterministic. It provides:

- keyword signals for curiosity, benefit, controversy and numbers;
- local B-roll matching against a local B-roll folder by filename keyword;
- optional emoji rules;
- baseline headline extraction;
- confidence thresholds so B-roll is not forced into a clip when there is no good match.

No stock-video scraping or cloud stock API is used.

## Custom fonts

`fonts.py` supports `.ttf`, `.otf`, `.woff`, and `.woff2` with file-signature and minimum-size validation plus deterministic hashed storage. Invalid formats are rejected. A renderer can fall back to a system font when a requested font is unavailable.

## Primary workflow

`POST /youtube/preview` -> `POST /youtube/import` -> `POST /analyze/{job_id}` -> `POST /render/{job_id}` -> `GET /download/{job_id}`

`POST /fonts` and `GET /fonts` manage local font assets.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: local file upload ceiling
- `MAX_VIDEO_DURATION_SECONDS`: maximum source duration for YouTube import
- `DOWNLOAD_TIMEOUT_SECONDS`: yt-dlp timeout

## Design principle

The URL is only an input transport. Once downloaded, **AI analysis remains local**. No OpenAI, Anthropic, Gemini, Groq, ElevenLabs, or other paid AI API is required for the V5 path.

The score is a **heuristic ranking**, not a prediction of TikTok, Reels, Shorts, or any other platform ranking algorithm.

## Engineering status

Implemented: URL-first import, local transcription, heuristic ranking, Smart EDL, subject-tracking baseline, virtual-camera path, advanced caption engine, three caption presets, custom-font validation, and local visual-intelligence planning.

Still required before production-grade claims: direct FFmpeg camera-path integration, robust multi-person identity tracking, semantic local B-roll retrieval, deeper headline/emoji composition, automated real-media render regression, performance profiling, and benchmark-based optimization against a fixed dataset.
