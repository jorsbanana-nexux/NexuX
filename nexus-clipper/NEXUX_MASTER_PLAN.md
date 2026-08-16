# NexuX Master Evolution Plan

Status: ACTIVE
Baseline: `main` @ `8863837eaea2e8b35eb003357c9279e9c5e0266e`

## Mission

NexuX is being evolved from an automatic short-form clipping engine into a local-first multimodal autonomous editorial system.

The goal is not feature-count parity with a commercial editor. The goal is a system that can understand source media, infer editorial intent, generate and compare alternatives, execute edits, critique its own result, revise it, validate the final media, and learn user preferences over time.

## Non-negotiable principles

1. Add before replace. Preserve working capabilities unless replacement is demonstrably safer or better.
2. One canonical runtime and one source of truth for each responsibility.
3. No fake capability. A planning stub, adapter, or unavailable dependency must never present as a successful media operation.
4. Every important decision has score, confidence, evidence, and reason where applicable.
5. Every final render passes media QA before completion.
6. Local-first remains the default. External AI is optional enhancement, not a hard dependency for the core pipeline.
7. Legacy code may remain during migration, but it cannot silently become canonical.
8. Quality claims require reproducible evidence and matched evaluation conditions.
9. Optimize correctness and editorial quality before aggressive performance optimization.
10. Human override remains possible at every consequential editorial decision.

## Target system loop

`ingest -> understand -> build analysis world -> generate candidates -> infer intent -> editorial rank -> plan timeline -> edit -> render -> critique -> revise -> QA -> package -> publish/measure -> learn`

## Program phases

### Phase 0 — Control Plane

Repository baseline, capability matrix, target architecture, quality contracts, roadmap, and migration boundaries.

### Phase 1 — Canonical Convergence

Reduce hidden orchestration, isolate compatibility layers, define stable service boundaries, unify runtime/version metadata, and make the canonical pipeline explicit.

### Phase 2 — Analysis World

Strengthen Analysis Bundle as the canonical multimodal evidence graph: transcript, words, speakers, scenes, subjects, audio, OCR, semantics, and confidence.

### Phase 3 — Editorial Brain

Upgrade candidate generation and ranking from heuristic-only scoring into layered deterministic + multimodal + bounded AI editorial reasoning.

### Phase 4 — Creative Directors

Deepen camera, audio, caption, visual treatment, cleanup, music/SFX, and platform-specific editing policies.

### Phase 5 — Autonomous Editing

Introduce robust timeline planning, alternative generation, self-critique, revision actions, and best-of-version selection.

### Phase 6 — Personal Editorial Intelligence

Capture explicit user preferences, overrides, accepted/rejected candidates, and style profiles without compromising privacy or local-first behavior.

### Phase 7 — Benchmark Lab

Automate real-media evaluation against human references and deterministic baselines. Add category-level commercial comparisons only under matched-source, reproducible protocols.

### Phase 8 — Performance & Hardware Adaptation

Cache/reuse, parallelism, batching, GPU/CPU adaptation, long-video benchmarks, memory controls, and failure recovery.

### Phase 9 — Frontier Creative System

Research-grade capabilities: richer audiovisual reasoning, stronger simulation of editorial alternatives, adaptive policies, and cross-modal creative planning.

## Required delivery state for a capability

`PLANNED -> IMPLEMENTED -> TESTED -> BENCHMARKED -> PROVEN`

A capability is not considered mature merely because code exists.

## Current baseline truth

Canonical Local-First V5/V6 code already contains strong foundations for targeted retrieval, transcription, multimodal analysis, editorial ranking, subject-aware camera, timeline rendering, critic metadata, analytics, and QA. Some compatibility/legacy modules remain partial or planning-only and must not be treated as equivalent to canonical production behavior.

## Immediate next actions

1. Finalize the capability matrix.
2. Finalize target architecture contracts.
3. Identify canonical/compatibility/legacy ownership for every high-impact module.
4. Establish the first benchmark corpus and editorial quality gates.
5. Only then begin behavior-changing code work in focused increments.
