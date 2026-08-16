# Phase 11 — Multimodal Model Upgrade & Local AI Model Orchestration

Adds a vendor-neutral local model control plane.

## Components
- Model registry with task/modality capabilities.
- Deterministic routing using quality/speed/VRAM constraints.
- Local model orchestrator with explicit handlers and graceful fallback.
- Confidence calibration hook.
- Regression tests.

No model binary is bundled and no cloud provider is required. Production perception engines remain unchanged until a concrete adapter is registered and benchmarked.
