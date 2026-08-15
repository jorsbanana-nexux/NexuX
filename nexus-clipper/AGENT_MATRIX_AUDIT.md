# NexuX 25-Agent Matrix Audit

This document is intentionally conservative. An agent is not considered production-integrated merely because it returns a successful dictionary.

## Canonical product mode

The canonical product is **Local-First V5 clipping without B-roll**. Its production path is:

`YouTube -> local download -> local transcription -> semantic + audio + vision analysis -> editorial ranking -> Smart EDL -> subject-aware camera -> captions -> FFmpeg -> render QA`

## Agent status

| Agent | Current truth | Policy |
|---|---|---|
| 01 Master Brain | Orchestration shell; does not execute the V5 pipeline | Compatibility only; do not claim as render engine |
| 02 URL Fetcher | Real yt-dlp downloader/validator | Useful compatibility component; V5 has its own hardened downloader |
| 03 Keyword Optimizer | Deterministic keyword expansion only | Research/metadata utility; not clip ranking |
| 04 Content Planner | Template planner for generated scripts | Generation-mode utility; not source-video clipping |
| 05 Competitor Analyzer | Static heuristic template, no competitor data ingestion | Not production intelligence yet |
| 06 Narration Writer | Generates synthetic narration text | Generation-mode only; never silently replaces source speech |
| 07 Voice Cloner | edge-tts network synthesis | Optional non-local feature; excluded from zero-cost/local-first core |
| 08 Emotion Controller | Keyword-based emotion mapping | Candidate enrichment utility; not a media renderer |
| 09 Spatial 8D Audio | Metadata-only placeholder; does not transform audio | Must not be called production audio processing |
| 10 Breath Injector | Returns injection points only | Generation-mode planning utility |
| 11 Scene Segmenter | Real media-backed scene detection adapter | Compatibility adapter over V5 vision; not the canonical pipeline entrypoint |
| 12 Subject Tracker | Real media-backed subject observations | Compatibility adapter over V5 vision; not the canonical pipeline entrypoint |
| 13 Visual Quality Checker | Real media-backed visual quality inspection | Compatibility adapter over V5 QA; watermark removal is not supported |
| 14 Lip Sync | Explicit GPU placeholder; no lip-sync transform | Disabled in canonical clipper mode |
| 15 B-roll Blocker | Real policy guard | Active as a guard; B-roll remains forbidden |
| 16 Subtitle Designer | Builds text/SRT metadata only | V5 captions renderer is canonical |
| 17 Sound Designer | Produces SFX plan only; no audio asset/render step | Disabled until connected to real local assets |
| 18 Music Selector | Produces genre/ducking plan only | Disabled until a real local music source is provided |
| 19 Transition AI | Produces transition labels only | Disabled until connected to real scene/timeline transforms |
| 20 Professional Editor | Legacy compatibility wrapper; evasion transforms removed | Isolated from canonical rendering and rejects evasion parameters |
| 21 Quality Inspector | Real media-backed post-render inspection | Compatibility adapter over V5 QA |
| 22 Audience Predictor | Static heuristic with hard-coded weights | V5 scorer is canonical; this is not a platform prediction model |
| 23 Auto Improver | Retry decision only; no actual improvement transform | Disabled until a concrete improvement strategy exists |
| 24 Omni Exporter | Generates export plans only | V5 compositor/export path is canonical |
| 25 SEO Generator | Random metadata template | Optional metadata utility; not part of render correctness |

## Zero-cost rule

The canonical V5 pipeline does not require paid cloud AI APIs. Network access is limited to source acquisition through yt-dlp. Local Whisper, OpenCV, FFmpeg, PySceneDetect, semantic/audio/vision heuristics, and deterministic render logic remain the core.

## No-B-roll rule

No agent may fetch, generate, synthesize, or insert B-roll automatically. Agent 15 is a guard, not a feature provider.

## Integrity rules

Agent 11 must not fabricate scene timestamps. Agent 12 must not return hard-coded subject coordinates. Agent 13 must not return fixed quality scores. Agent 21 must not return fixed PASS checks. Agent 20 must not contain fingerprint-evasion transforms such as speed shifts, flips, saturation tricks, or zoom-based evasion. These invariants are enforced by the V5 quality gate.

## Remaining hardening targets

1. Connect only those compatibility agents that have a concrete local capability to canonical V5 contracts.
2. Keep planning-only agents isolated until they produce real artifacts used by a stage.
3. Add broader adapter coverage for the remaining compatibility agents without creating a second rendering pipeline.
4. Continue real-media end-to-end validation on representative source videos.
