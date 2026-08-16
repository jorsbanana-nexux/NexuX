# Phase 4A — Story Plan Contract

Phase 4A introduces the immutable, versioned `StoryPlan` contract.

## Purpose
A StoryPlan describes an editorial strategy before any render occurs. It may choose an opening, setup, escalation, core, revelation, payoff, and ending from existing evidence.

## Contract rules
- Versioned and immutable.
- Every plan has a job id and stable plan id.
- Quality fields are normalized to `[0,1]`.
- Evidence, reasons, and risks are explicit.
- Decision is one of `DRAFT`, `KEEP`, `REFINE`, `REJECT`, `REVIEW`.
- A StoryPlan is not an EDL and must not imply that media has already been edited or rendered.
- No superiority claim is permitted without benchmark evidence.

## Next
4B will generate multiple competing plans from an `AnalysisWorld` while keeping this contract stable.
