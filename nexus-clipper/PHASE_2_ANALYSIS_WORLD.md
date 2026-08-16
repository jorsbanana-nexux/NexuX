# Phase 2 — Analysis World

Goal: establish one authoritative, immutable, versioned evidence artifact for every source job.

## Contract

`AnalysisWorld` unifies media, transcript, scenes, subjects, audio evidence, candidates, editorial intent, provenance, and confidence metadata.

## Principles

- one source of truth per job
- immutable snapshots after construction
- explicit schema version
- evidence/provenance attached to derived observations
- graceful omission of unavailable modalities
- no silent synthetic success
- canonical pipeline consumes the world rather than parallel ad-hoc dictionaries

## Phase 2 slices

1. World schema and validation
2. Provenance/confidence model
3. Canonical builder and persistence
4. Pipeline integration
5. Retrieval/render projections
6. Regression and schema compatibility tests

## Definition of Done

- canonical pipeline creates and persists one `AnalysisWorld` artifact
- transcript, media, scenes, subjects, audio, candidates and editorial decision reference the same world snapshot
- schema validation rejects malformed worlds
- compatibility API exposes the persisted world without creating a second analysis authority
- tests cover immutability, serialization, missing modalities and schema compatibility
