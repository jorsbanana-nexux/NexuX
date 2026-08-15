# V5 Virtual Camera

The virtual-camera subsystem converts sampled face observations into a smoothed normalized camera path for 9:16 output.

## Design

1. Normalize detections into `SubjectObservation`.
2. Choose a primary subject with temporal continuity and confidence checks.
3. Derive a crop window that keeps the subject inside frame bounds.
4. Smooth camera center using bounded exponential motion.
5. Fall back to a deterministic center path when no subject is available.

This is a baseline, intentionally modular tracker. A stronger detector/tracker can replace `normalize_legacy_faces()` without changing the camera-path interface.

## Non-goals

This does not claim identity-level multi-person tracking, pose-aware composition, or platform-specific crop behavior yet. Those belong in the next vision-hardening layer.
