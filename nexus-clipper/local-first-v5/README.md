# NexuX Local-First V5

Local-first backend baseline beside the legacy NexuX engine. The preferred input is now a **YouTube URL**; local file upload remains a fallback.

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

```text
YouTube URL
  -> yt-dlp LOCAL DOWNLOAD
  -> FFprobe validation
  -> faster-whisper LOCAL transcription
  -> word timestamps
  -> candidate generation
  -> weighted heuristic ranking
  -> ASS subtitles
  -> FFmpeg H.264/AAC
```

### 1. Preview a YouTube URL

`POST /youtube/preview`

```json
{"url":"https://www.youtube.com/watch?v=VIDEO_ID","max_height":1080}
```

### 2. Import the YouTube video locally

`POST /youtube/import`

The server uses `yt-dlp` on the local machine. No YouTube API key and no paid cloud API are required. Playlist URLs and live streams are intentionally rejected in this V5 baseline.

### 3. Analyze

`POST /analyze/{job_id}`

### 4. Render the top selected clip

`POST /render/{job_id}`

### 5. Download

`GET /download/{job_id}`

## Optional local file fallback

`POST /upload` remains available for MP4/MOV/MKV/WebM/AVI input.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: local file upload ceiling
- `MAX_VIDEO_DURATION_SECONDS`: maximum source duration for YouTube import
- `DOWNLOAD_TIMEOUT_SECONDS`: yt-dlp timeout

## Design principle

The URL is only an input transport. Once downloaded, **all AI analysis remains local**. The local source becomes the canonical media artifact used by FFprobe, Whisper, vision, scoring, editing, and rendering.

The score is a **heuristic ranking**, not a prediction of TikTok, Reels, Shorts, or any other platform ranking algorithm.

## Current baseline limitations

This is still an engineering baseline. The next layers are: timeline-aware silence/filler/repetition removal with exact subtitle remapping, multi-face identity tracking and virtual-camera smoothing, sentence-grouped karaoke captions, custom fonts, B-roll keyword matching, headline/emoji rules, and automated render regression tests.
