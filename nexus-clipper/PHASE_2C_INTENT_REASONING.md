# Phase 2C — Intent & Editorial Reasoning

## Goal

Turn user intent into a first-class editorial decision input. `AnalysisWorld.editorial.intent` is now the canonical representation consumed before multimodal ranking.

## Intent contract

- objective: `viral`, `educational`, `storytelling`, `emotional`, `authority`, or a custom objective
- audience
- platform
- tone
- style
- target duration
- clip limit
- required topics
- excluded topics
- optional preference weights

## Decision flow

```text
User request
  -> EditorialIntent
  -> AnalysisWorld.editorial.intent
  -> deterministic intent reasoning
  -> candidate pool
  -> existing multimodal editorial ranker
  -> final diverse selection
```

The phase deliberately preserves the existing ranker. Intent is a decision layer, not a rewrite of proven multimodal scoring.

## Evidence and explainability

Each selected candidate can carry:

- `intent_reasoning.intent_score`
- required-topic match
- excluded-topic match
- duration fit
- objective
- human-readable reasons
- intent payload
- AnalysisWorld provenance

## Safety of migration

The old `select_diverse_from_world` API remains intact. The canonical generation pipeline uses `select_diverse_from_world_with_intent` during Phase 2C. Existing callers can migrate independently.

## Definition of Done

- [x] Intent contract exists.
- [x] API request exposes intent fields.
- [x] Job persists intent.
- [x] AnalysisWorld persists intent.
- [x] Intent reasoning is deterministic and testable.
- [x] Canonical pipeline uses intent-aware selection.
- [x] Selected clips retain intent + world lineage.
- [x] Regression tests cover required/excluded topics and lineage.
- [ ] CI green.
- [ ] Human benchmark proves improvement over intent-blind baseline.
