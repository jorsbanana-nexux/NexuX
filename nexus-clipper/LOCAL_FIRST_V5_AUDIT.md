# NexuX Local-First V5 Audit

## Key findings

The existing NexuX backend has a useful FastAPI/React/engine foundation, but the legacy path is not strictly local-first: its requirements include cloud SDKs and the content analyzer can call Gemini when a key is available. The main pipeline is also YouTube-first and its job registry is process-memory based.

## V5 target

Upload -> FFprobe validation -> faster-whisper local transcription -> word/segment timestamps -> heuristic content analysis -> candidate generation -> weighted heuristic ranking -> local face/framing baseline -> ASS subtitles -> H.264/AAC MP4.

Viral Score is explicitly heuristic ranking, not a prediction of TikTok, Reels, Shorts, or any platform algorithm.

Weights:
- Hook 0.34
- Engagement 0.28
- Visual 0.16
- Clarity 0.14
- Duration Fit 0.08

Hook signals:
curiosity, question, controversy, emotional language, surprising statement, number/statistic, direct benefit, unusual claim, urgency, contradiction.

## Hardening priorities

1. Strict local-only dependency set.
2. Persistent job state and artifacts.
3. Safe upload and path validation.
4. Deterministic fallback when local AI/vision is unavailable.
5. Timeline edit-list engine for silence/filler removal with subtitle mapping.
6. Multi-face identity tracking and virtual-camera smoothing.
7. Sentence-level karaoke ASS rendering with active-word highlight.
8. Local semantic reranker/embeddings for context and payoff scoring.
9. Render regression tests and benchmark dataset.

## Known limits

This is not claimed to be a commercial-platform replacement yet. Advanced semantic repetition removal, learned ranking, lip-aware editing, and high-confidence multi-person tracking require additional local models and benchmark validation.
