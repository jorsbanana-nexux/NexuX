# NexuX Local-First V5

This is an isolated local-first backend baseline added beside the legacy NexuX engine. It is intended for further hardening without changing the existing `main` implementation.

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

## Pipeline

`POST /upload` -> local `faster-whisper` transcription -> heuristic candidate generation -> weighted heuristic ranking -> ASS subtitles -> FFmpeg H.264/AAC render.

The score is a heuristic ranking and must not be described as a prediction of any social platform algorithm.

## Environment

- `WHISPER_MODEL`: `tiny`, `base`, `small`, `medium`, `large-v3`
- `WHISPER_DEVICE`: `cpu` or `cuda`
- `WHISPER_COMPUTE`: e.g. `int8` or `float16`
- `MAX_UPLOAD_MB`: upload ceiling

## Current baseline limitations

The first V5 layer intentionally keeps the implementation conservative. Smart multi-face identity tracking, timeline-aware silence/filler removal, advanced semantic reranking, B-roll matching, custom fonts, and advanced subtitle safe-zone avoidance remain subsequent hardening targets.
