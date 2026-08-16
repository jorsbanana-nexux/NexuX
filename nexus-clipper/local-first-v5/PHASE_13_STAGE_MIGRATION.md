# Phase 13 — Stage Migration & Full E2E Wiring

This milestone moves existing NexuX implementations behind the Phase 12 autonomous stage contract.

## Concrete adapters

- ingest — validates source/job context
- transcribe — caption-first retrieval with local Whisper fallback
- analyze — existing candidate generation
- reason — existing editorial intelligence
- plan — existing diverse ranker
- direct — Phase 6 directive state
- render — explicit injected canonical renderer
- critic — existing multimodal critic
- revise — existing revision action generator
- publish — existing publish-plan builder
- feedback — explicit feedback artifact

## Safety

The renderer remains explicitly injected. No adapter fabricates a rendered artifact. Missing dependencies fail closed. The legacy `canonical_v6_pipeline.run_generation` remains available for parity comparison until the concrete stage path is proven equivalent.

## Acceptance

A stage is migration-ready only when its adapter has:

1. contract tests,
2. provenance output,
3. parity evidence against the legacy implementation,
4. deterministic failure behavior,
5. no hidden dependency on the compatibility API.
