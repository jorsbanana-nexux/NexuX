# Phase 3C — Adaptive Context Expansion & Semantic Promise→Payoff Verification

## Objective
Replace a fixed context window with evidence-driven expansion. The engine starts narrow, measures uncertainty, expands only when necessary, and stops when the promise/payoff relationship is sufficiently supported or the evidence budget is exhausted.

## Contract
Every adaptive decision records initial/final radius, expansion count, semantic promise, semantic payoff, semantic relation score, uncertainty, confidence, and stop reason.

## Guardrail
The semantic relation in this slice is a deterministic lexical/temporal proxy. It is not a claim of deep semantic understanding. Future local embedding/VLM/LLM verification can replace or augment the implementation without changing the contract.
