# Phase 3C — Adaptive Context Expansion & Semantic Promise→Payoff Verification

## Objective
Replace the fixed contextual window with evidence-driven expansion. The system starts narrow, measures uncertainty, expands only when necessary, and stops when the promise/payoff relationship is sufficiently supported or the configured evidence budget is exhausted.

## Components
- `adaptive_context.py`
- adaptive integration into `intent_aware_selection.py`
- semantic promise→payoff relation proxy
- uncertainty calculation
- expansion budget and stop reasons
- regression tests

## Contract
Every adaptive decision records:
- initial/final radius
- expansion count
- semantic promise
- semantic payoff
- semantic relation score
- uncertainty
- confidence
- stop reason

## Guardrail
The semantic relation implemented in this slice is a deterministic lexical/temporal proxy, not a claim of deep semantic understanding. Future slices may replace or augment it with local embeddings, a local VLM/LLM, or a calibrated learned verifier without changing the contract.

## Decision principle
`KEEP` is not granted merely because a payoff token is found. The engine must have sufficient context integrity, relation evidence, and confidence. Otherwise it expands, refines, or reports uncertainty.
