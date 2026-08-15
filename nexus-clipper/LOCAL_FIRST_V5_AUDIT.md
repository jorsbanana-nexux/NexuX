# NexuX Local-First V5 Audit

## Legacy findings

The existing NexuX backend has a useful FastAPI/React/engine foundation, but the legacy path is not strictly local-first: its requirements include cloud SDKs and its content analyzer can optionally call Gemini. The legacy job registry is process-memory based.

## V5 architecture

`YouTube URL -> local yt-dlp -> FFprobe -> faster-whisper -> content intelligence -> heuristic ranking -> Smart EDL -> subject tracking -> virtual camera -> captions -> headline/emoji -> FFmpeg`

B-roll is intentionally excluded from V5.

## Ranking contract

Viral Score is a heuristic ranking score, not a prediction of TikTok, Reels, Shorts, or any platform algorithm.

`Viral = Hook*0.34 + Engagement*0.28 + Visual*0.16 + Clarity*0.14 + DurationFit*0.08`

Hook factors include curiosity, question, controversy, emotional language, surprising statement, number/statistic, direct benefit, unusual claim, urgency, and contradiction.

## Timeline contract

The EDL is the canonical timeline. Every output-time subtitle, camera point, and rendered cut must derive from the same source-to-output mapping. This prevents audio/video/subtitle drift when silence/filler/repetition cuts are applied.

## Quality contract

The branch now has deterministic tests plus a real synthetic-media FFmpeg regression that verifies final composition produces a valid 1080x1920 MP4 with both audio and video streams.

A target-machine real-video run and a human-rated benchmark corpus remain mandatory before making any production-quality or commercial-superiority claim.
