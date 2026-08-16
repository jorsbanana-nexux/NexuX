# Phase 2B — Editorial World Consumption

Goal: make the canonical editorial engine consume `AnalysisWorld` as its primary evidence surface.

## Scope

- Adapt immutable `AnalysisWorld` into explicit editorial evidence.
- Feed candidate text, temporal bounds, audio evidence, vision evidence, semantics, intent, confidence, and provenance through one context object.
- Preserve current ranker interfaces through compatibility adapters while migration is incremental.
- Record editorial decisions against the world identifier/schema for traceability.

## Rule

`AnalysisWorld` is authoritative for evidence once complete. Legacy ad-hoc arguments remain compatibility inputs only and must not silently override world evidence.

## Next

Migrate editorial ranking and AI rejudge to consume `ranking_context(world)` directly, then remove duplicated evidence assembly.
