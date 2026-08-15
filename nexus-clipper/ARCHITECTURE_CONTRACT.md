# NexuX Architecture Contract

## Source of truth

Local-First V5 is the only production clipping engine. `canonical_api.py` is the only public API entrypoint for the V5 runtime.

`server.py` is an internal compatibility runner used by the canonical API. It must not be presented as a second public product surface.

The legacy `backend/` tree and `build_nexus.py` are compatibility/legacy tooling only. They are not part of the canonical runtime path.

## Canonical flow

`source -> ingest -> transcription -> analysis bundle -> editorial ranking -> EditTimeline -> camera/captions -> FFmpeg -> render QA -> output artifact`

Every stage must produce an explicit artifact or structured result consumed by a later stage.

## Product invariants

1. Local-first: no paid cloud AI is required for canonical clipping.
2. No B-roll: the canonical engine never fetches, creates, synthesizes, or inserts B-roll.
3. One job identity: every artifact belongs to one persistent job id.
4. One timeline: video, audio, camera, and captions derive from the same EditTimeline.
5. One renderer: FFmpeg is the canonical media compositor.
6. One QA gate: a render cannot become `completed` before media inspection passes.
7. UI is not the source of truth: future UI designs may replace the current shell without changing the engine contract.

## Legacy policy

Legacy files may remain temporarily for compatibility, migration, or historical reference, but they must not be documented as canonical and must not be used by the launcher.

Planning-only agents are not production pipeline stages. They must never return synthetic success that looks like a completed media operation.
