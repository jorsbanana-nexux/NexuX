# NexuX Target Architecture

## Objective

Create one canonical editorial system while preserving compatibility during migration.

## Canonical layers

```text
API / UI
   -> Application Service
      -> Job Orchestrator
         -> Media Ingest
         -> Analysis World
         -> Editorial Intelligence
         -> Edit Planner
         -> Creative Directors
         -> Renderer
         -> Critic / Revision
         -> QA Gate
         -> Packaging / Publishing
         -> Analytics
```

## Source-of-truth ownership

### Application Service
Owns request validation, job lifecycle, cancellation, and response contracts.

### Job Orchestrator
Owns sequencing, retries, stage transitions, resumability, and artifact references.

### Analysis World
Owns the persisted multimodal evidence bundle. Downstream modules consume evidence rather than re-running analysis unnecessarily.

### Editorial Intelligence
Owns candidate generation, feature extraction, deterministic ranking, AI rejudge, intent matching, confidence, evidence, and diversity.

### Edit Planner
Owns the `EditTimeline`/EDL. Video, audio, camera, captions, overlays, and cleanup must derive from the same timeline.

### Creative Directors
Own policy and decisions for camera, audio, captions, music/SFX, optional B-roll, voice-over, layouts, and platform style.

### Renderer
FFmpeg is the canonical compositor. No parallel hidden renderer should become production truth.

### Critic / Revision
Evaluates rendered artifacts, emits structured defects, maps defects to executable revision actions, and can request a bounded new render.

### QA Gate
Only QA can promote a render to `completed`.

## Artifact contract

Every significant stage produces one of:

- structured artifact
- persisted state transition
- explicit failure
- explicit skip/degraded state

A planning-only result must never masquerade as a completed media artifact.

## Decision contract

Where an AI/editorial decision is material, it should expose:

```text
score
confidence
evidence
reason
risks
decision
```

## Compatibility rule

Legacy/compatibility modules may call canonical services through adapters. Canonical services must never depend on legacy module behavior that can silently diverge.

## Runtime convergence rule

The final launch path must have one documented canonical entrypoint. Compatibility runners may remain temporarily, but they are not product truth.

## Security/local-first rule

Local execution must bind to loopback by default. External AI providers are optional and isolated behind a provider contract. Provider credentials never reach the frontend.

## Performance rule

Analysis artifacts should be reusable by downstream stages. Avoid repeated decoding, transcription, scene scans, or vision inference when the same evidence already exists.

## Revision loop

```text
source
 -> analysis
 -> candidate
 -> edit plan
 -> render v1
 -> critic
 -> revision plan
 -> render v2 (bounded)
 -> critic
 -> best version
 -> QA
```

## Migration strategy

1. Document current ownership.
2. Create service boundaries around existing canonical implementations.
3. Redirect compatibility callers through those boundaries.
4. Add tests for parity.
5. Remove only proven-dead orchestration.
6. Keep user-visible behavior stable during migration unless a benchmarked improvement is intentional.
