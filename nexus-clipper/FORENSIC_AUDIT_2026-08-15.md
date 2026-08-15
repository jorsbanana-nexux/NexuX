# NexuX Forensic Audit — 2026-08-15

## Scope

Audited the repository tree, canonical Local-First V5 runtime, compatibility API, legacy backend, 25-agent matrix, frontend contract, installers/launchers, dependencies, quality gate, tests, and GitHub Actions wiring.

## Confirmed architecture

Canonical product mode is Local-First V5 clipping without B-roll. The repository still contains a substantial legacy backend and 25-agent compatibility matrix; these are not equivalent to the canonical production path.

The repository contains both `local-first-v5/app.py` and `local-first-v5/server.py`. `app.py` contains the core analysis/render API; `server.py` is the frontend compatibility/background-job adapter. This duplication is intentional for compatibility but is a maintenance risk and remains a hardening target.

## Defects found and fixed in this audit

1. **Queued cancellation race** — a cancellation flag could be overwritten when the background worker started. Fixed with sticky cancellation initialization plus a post-render cancellation check; regression test added.
2. **Local API exposure** — Windows and Unix launchers advertised loopback but bound Uvicorn to `0.0.0.0`. Fixed to `127.0.0.1` for local-first operation.
3. **Frontend duration contract mismatch** — UI offered 15–180 seconds while canonical candidate generation only supports 20–60 seconds. UI and API contract are now 20–60 seconds.
4. **Language control was cosmetic** — API accepted `language` but Whisper was not receiving it. Added a local transcription adapter that passes the selected language to faster-whisper.
5. **Quality gate coverage was incomplete** — quality gate only syntax-checked a subset of modules and did not require faster-whisper. It now covers canonical runtime modules and required local ML/media dependencies.
6. **Frontend was absent from CI** — GitHub Actions did not run `npm ci`/`npm run build`. Added frontend build verification.
7. **Main branch lacked automatic V5 validation on push** — workflow previously only triggered on PRs. Added push validation for `main`.

## Findings that are intentionally not mislabeled as fixed

### P0/P1 architecture hardening

- `server.py` and `app.py` remain two closely related runtime surfaces. They share modules but duplicate orchestration concerns.
- The legacy `backend/agents` directory contains 25 agents, several of which are explicitly non-production or placeholders. `AGENT_MATRIX_AUDIT.md` records this conservatively.
- Agent 11/12/13/21 in the legacy tree must not be treated as equivalent to the real V5 vision/QA modules.
- Agent 20 contains legacy evasion parameters and is excluded from canonical mode.

### Functional contract gaps

- `normalize_audio` remains an accepted compatibility request field but does not yet control an explicit normalization stage.
- The canonical audio intelligence module exists and Smart EDL stores its profile, but audio profile signals are not yet fully incorporated into candidate ranking in every runtime surface.
- The legacy API and canonical API have different feature surfaces; future work should converge these rather than expanding compatibility-only behavior.

### Verification limits

- Deterministic tests cannot prove editorial superiority on arbitrary real videos.
- A real target-machine end-to-end run with an actual downloaded video and local Whisper model is still required for deployment confidence.
- No claim of zero defects is possible until real-media, multi-platform, multi-format testing is performed.

## Current confidence

The repository is materially safer and more internally consistent than before this audit. CI now validates both backend/V5 and frontend on `main` pushes. The remaining hardening work is primarily consolidation of runtime surfaces and removal/replacement of legacy placeholder agents, not basic correctness of the canonical V5 path.
