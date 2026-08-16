# Phase 1B — Media Ingest, Transcription & Audio Extraction

## Scope

This slice moves three capability owners behind the canonical runtime boundary without deleting compatibility code:

- `media_ingest.py` — source validation, YouTube metadata probe, full retrieval, local media inspection.
- `transcription_service.py` — canonical transcription boundary over the existing faster-whisper worker/local implementation.
- `audio_service.py` — canonical audio analysis boundary and normalized editorial signals.

## Canonical runtime

`runtime_adapter.py` now owns explicit dependencies for:

- `probe_youtube`
- `ingest_youtube`
- `transcribe_local`
- `analyze_audio`
- `audio_signals`

Downstream canonical code must consume these contracts rather than importing `youtube.py`, `transcription.py`, or `audio_intelligence.py` directly for orchestration.

## Editorial evidence

The canonical V6 pipeline now records `audio_profile` and `audio_signals` for each targeted candidate render. These become persistent job evidence and can be consumed by the editorial critic and later ranking improvements.

The first extraction intentionally does not change the pre-retrieval candidate ordering because targeted retrieval is a core local-first performance property. A later editorial phase can add an audio-aware shortlist reranker without coupling the pipeline back to the low-level audio implementation.

## Compatibility

Existing legacy modules remain in place. Their behavior is not deleted as part of this slice. The goal is to converge ownership first, then remove duplication only after parity and regression tests pass.

## Definition of Done

- [x] Ingest service exists with explicit contracts.
- [x] Transcription service exists with explicit validation of returned transcript shape.
- [x] Audio service exists with profile + normalized signal APIs.
- [x] Canonical runtime binds to all three services.
- [x] Canonical pipeline persists audio evidence.
- [x] Boundary regression tests cover service ownership.
- [ ] GitHub Actions passes for the final Phase 1B head.
- [ ] Legacy low-level imports removed from compatibility façade where safe.
