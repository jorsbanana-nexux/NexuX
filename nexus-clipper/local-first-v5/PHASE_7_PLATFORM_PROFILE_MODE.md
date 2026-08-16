# Phase 7 — Platform Intelligence + Personal Editorial Profiles + Adaptive Creative Modes

Adds a renderer-agnostic policy layer.

## Platform policy
- TikTok, YouTube Shorts, Instagram Reels, LinkedIn, X, generic fallback.
- Duration, aspect ratio, pacing, caption density, hook/context/visual biases.

## Personal profile
- Immutable `EditorialProfile`.
- Profile overrides are explicit and deterministic.

## Creative modes
- viral
- educational
- storytelling
- authority
- balanced

## Guardrails
- Policies are decision inputs, not platform-performance guarantees.
- Existing media/rendering code is not replaced.
- No synthetic render success.
