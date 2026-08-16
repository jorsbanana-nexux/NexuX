# Phase 5 — Autonomous Edit Execution, Critic & Revision

This batch adds a bounded, renderer-agnostic autonomous edit loop.

## Flow

`StoryPlan -> render state -> critic -> quality gate -> revision actions -> renderer -> critic`

## Guarantees

- bounded attempts
- explicit PASS / REVIEW outcomes
- revision actions with priority and evidence
- no synthetic success
- the revision callbacks own actual media mutation/rendering
- existing renderer remains unchanged

## Components

- `autonomous_edit_session.py` — immutable iteration/session contract
- `revision_engine.py` — normalized revision actions
- `edit_quality_gate.py` — publish eligibility gate
- `autonomous_editor.py` — orchestration
- `tests/test_phase5_autonomous_edit.py` — regression coverage
