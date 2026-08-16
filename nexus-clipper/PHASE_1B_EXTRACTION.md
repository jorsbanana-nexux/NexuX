# Phase 1B — Runtime Extraction

## Goal

Extract low-level runtime ownership from the compatibility `server.py` façade while preserving user-visible behavior and existing pipeline implementations.

## Extracted owners

- `job_service.py`: durable job state and cancellation registry.
- `engine_media.py`: canonical FFprobe primitive.
- `render_service.py`: canonical media render orchestration.
- `vision_service.py`: canonical scene, subject, and visual-quality dispatch.

## Compatibility policy

`server.py` remains importable as a compatibility façade. Its legacy symbols delegate to the extracted service owners rather than maintaining independent implementations.

## Canonical policy

`runtime_adapter.py` binds the canonical runtime to extracted owners. Canonical pipeline code must not regain a dependency on `server.py`.

## Parity gate

Phase 1B is complete only when:

1. extracted services import without importing `server.py`;
2. canonical runtime uses extracted service callables;
3. compatibility façade resolves to the same service implementations;
4. deterministic tests pass;
5. CI validates the branch before merge.

## Remaining Phase 1B work

The next extraction slice should isolate audio/transcription and source-ingest primitives, followed by removal of remaining compatibility-only implementation code from `server.py`.
