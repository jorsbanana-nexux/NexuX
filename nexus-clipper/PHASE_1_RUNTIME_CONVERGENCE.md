# Phase 1 — Canonical Runtime Convergence

## Goal

Reduce orchestration coupling without discarding working NexuX functionality.

## Completed slice

- `contracts.py` is the shared source for `GenerateRequest` and `CompatJob`.
- `runtime_adapter.py` defines an explicit dependency boundary for the canonical pipeline.
- `application_service.py` owns canonical request validation and job lifecycle operations.
- `canonical_api.py` delegates lifecycle orchestration to `CanonicalApplicationService`.
- `canonical_v6_pipeline.py` consumes `CanonicalRuntime` instead of importing `server.py` directly.
- `server.py` consumes the shared contracts instead of defining duplicate API models.
- `test_runtime_convergence.py` protects these architectural boundaries.

## Compatibility strategy

The runtime adapter still bridges to existing `server.py` implementations. This is intentional: Phase 1 separates ownership first, then extracts individual implementations behind the new contracts.

## Remaining Phase 1 work

1. Extract filesystem/job-store primitives from `server.py` into canonical services.
2. Move renderer ownership out of the compatibility module.
3. Move vision/audio capability ownership out of compatibility imports.
4. Remove remaining `server.py` imports from canonical modules.
5. Add parity tests between compatibility and canonical paths.
6. Verify local-first startup and job lifecycle on the target OS.

## Definition of done

The canonical launch path must no longer depend on compatibility orchestration for request lifecycle, rendering ownership, or capability dispatch. Compatibility callers may depend on canonical services; the reverse dependency is forbidden.
