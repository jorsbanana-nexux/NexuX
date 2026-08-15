# NexuX Local-First V5

Local-first clipping backend staged beside the legacy NexuX implementation.

## Pipeline

`YouTube URL -> local yt-dlp -> FFprobe -> faster-whisper -> heuristic content analysis -> candidate ranking -> Smart EDL -> subject-aware camera path -> advanced ASS captions -> FFmpeg export`

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

## Primary workflow

```text
YouTube URL
  -> yt-dlp LOCAL DOWNLOAD
  -> FFprobe validation
  -> faster-whisper LOCAL transcription
  -> word timestamps
  -> candidate generation
  -> weighted heuristic ranking
  -> Smart EDL
  -> subject-aware camera path
  -> advanced ASS captions
  -> FFmpeg H.264/AAC
```

## Caption presets

- `karaoke`: phrase-grouped captions, active-word highlight and subtle pop scaling.
- `pop_line`: bold high-contrast treatment with stronger keyword emphasis.
- `deep_diver`: restrained presentation with emphasis focused on important keywords.

The caption engine consumes the canonical edited timeline when available, so removed source ranges do not cause subtitle drift.

## Custom fonts

`fonts.py` supports `.ttf`, `.otf`, `.woff`, and `.woff2` with signature/size validation and deterministic hashed storage. Invalid or unsupported files are rejected; renderer-level fallback should use a configured system font if a registered font cannot be resolved.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: local file upload ceiling
- `MAX_VIDEO_DURATION_SECONDS`: maximum source duration for YouTube import
- `DOWNLOAD_TIMEOUT_SECONDS`: yt-dlp timeout

## Design principle

The URL is only an input transport. Once downloaded, **all AI analysis remains local**. No OpenAI, Anthropic, Gemini, Groq, ElevenLabs, or other paid AI API is required for the V5 baseline.

The score is a **heuristic ranking**, not a prediction of TikTok, Reels, Shorts, or any other platform ranking algorithm.

## Current engineering status

Implemented: URL-first import, local transcription, heuristic ranking, Smart EDL, subject-tracking baseline, virtual-camera path, advanced caption engine, three caption presets, and custom-font validation.

Still required before production-grade claims: direct FFmpeg camera-path integration, robust multi-person identity tracking, local semantic B-roll matching, headline/emoji engine, automated render regression with real media fixtures, performance profiling, and benchmark-based optimization against a fixed dataset.
