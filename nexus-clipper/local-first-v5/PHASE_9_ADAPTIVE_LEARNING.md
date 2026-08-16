# Phase 9 — Adaptive Learning & Editorial Memory

Phase 9 adds a bounded personalization layer above deterministic/editorial scoring.

## Guarantees

- human feedback is stored as explicit events;
- old feedback decays over time;
- personalization is capped at a small score adjustment;
- empty or low-confidence profiles are a no-op;
- memory can be exported and rebuilt;
- baseline scoring remains the source of truth;
- personalization must remain removable/reversible;
- benchmark evaluation must compare baseline vs personalized behavior.

## Flow

`human feedback -> memory event -> profile -> bounded adjustment -> candidate decision -> benchmark`

No feedback event is treated as ground truth for virality or platform performance.
