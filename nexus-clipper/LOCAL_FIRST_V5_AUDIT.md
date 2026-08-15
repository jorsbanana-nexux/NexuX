# NexuX Local-First V5 Audit

## Key findings

The existing NexuX backend has a useful FastAPI/React/engine foundation, but the legacy path is not strictly local-first: its requirements include cloud SDKs and the content analyzer can call Gemini when a key is available. The main pipeline is also YouTube-first and its job registry is process-memory based.

## V5 progress

- URL-first local YouTube import via yt-dlp.
- FFprobe validation and persisted job state.
- Local faster-whisper word timestamps.
- Heuristic candidate ranking with explicit heuristic disclosure.
- Canonical EDL for silence/filler/repetition cuts and source-to-output remapping.
- Subject-tracking baseline and normalized virtual-camera path with smoothing/fallback.
- Advanced caption engine with phrase grouping, KARAOKE/POP LINE/DEEP DIVER presets, keyword emphasis, active-word animation, face-aware vertical margin heuristics, and custom font validation.

## Weights

- Hook 0.34
- Engagement 0.28
- Visual 0.16
- Clarity 0.14
- Duration Fit 0.08

## Remaining work before production claims

1. Integrate the virtual-camera path into the final FFmpeg filter graph.
2. Replace single-best-face sampling with persistent multi-person identity tracking.
3. Add semantic local B-roll indexing and confidence thresholds.
4. Add headline/emoji rules and safe-zone composition.
5. Add real-media rendering fixtures and objective quality/performance benchmarks.
6. Compare against a fixed commercial-editor benchmark set; do not claim superiority without measurements.

Viral Score is explicitly heuristic ranking, not a prediction of TikTok, Reels, Shorts, or any platform algorithm.
