# Phase 3B — Contextual Narrative Verification

## Goal
Prevent locally attractive clips from being accepted when they lose the surrounding narrative promise, dependency, or payoff.

## Slice
- bounded context retrieval around each candidate
- before/after context windows
- post-candidate resolution search
- promise→payoff semantic overlap proxy
- context integrity
- dependency score
- premature-cut risk
- unresolved-question risk
- KEEP / EXTEND / REFINE / REVIEW recommendation
- provenance and confidence
- integration into intent + narrative selection

## Design rule
Contextual verification is an evidence layer. It does not replace the multimodal ranker or claim human-level narrative understanding. A later benchmark decides whether its weighting should increase.

## Future
- wider adaptive context windows
- semantic embeddings / local reranking
- true promise→payoff relation verification
- cross-speaker context reconstruction
- contradiction and reference resolution
- narrative graph persistence in AnalysisWorld
