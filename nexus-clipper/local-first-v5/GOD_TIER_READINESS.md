# NexuX God-Tier Readiness Matrix

This document separates implemented invariants from claims that still require real-world evidence.

| Area | Current state | Evidence required before launch claim |
|---|---|---|
| Canonical API | Implemented | Clean-room startup test on target OS |
| Persistent jobs | Implemented | Crash/restart injection on target OS |
| Hard cancellation | Implemented | Download/transcription/render interruption tests |
| Whisper worker isolation | Implemented | Long-duration memory and restart test |
| Analysis Bundle | Implemented | Schema regression + mutation-proof tests |
| Audio reuse | Implemented | Call-count regression test |
| Scene analysis | Sequential scanner in canonical path | 1h/6h/10h timing benchmark |
| Subject analysis | Scoped to candidate windows | Representative-face benchmark |
| Timeline | Deterministic EDL | AV drift + cut-boundary corpus |
| Caption remap | Boundary-safe preparation | Human review of cut-crossing words |
| Render QA | Resolution/audio/duration/visual + AV packet checks | Real corpus + corrupt-output injection |
| Editorial ranking | Multi-signal deterministic ranking | Human-rated benchmark protocol |
| Virality prediction | Heuristic only | Never claim proprietary platform equivalence without evidence |
| B-roll | Explicitly forbidden | Policy regression tests |
| UI | Prototype shell only | Future design and integration pass |
| Legacy agents | Compatibility/utility surfaces | Explicit integrate/isolate/remove audit |
| Commercial equivalence | Not claimed | Matched-source blinded comparison |

## Launch terminology

Use "engineering-ready" when deterministic CI and target-machine tests are green.

Use "commercially competitive" only after matched-source human evaluation.

Use "superior to X" only when a predeclared, reproducible benchmark supports the claim.

## Validation discipline

The readiness state is governed by the CI result for the current branch head. A cancelled, stale, or superseded workflow run is not evidence for the current code state.
