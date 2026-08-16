from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class BoundaryScore:
    start: float
    end: float
    duration: float
    score: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "duration": round(self.duration, 3),
            "score": round(self.score, 3),
            "reasons": list(self.reasons),
        }


def _word_count(text: str) -> int:
    return len(text.split())


def _boundary_score(
    candidate: dict[str, Any],
    start: float,
    end: float,
    *,
    target_duration: float = 45.0,
    segment_lookup: Callable[[float, float], Iterable[dict[str, Any]]] | None = None,
) -> BoundaryScore:
    duration = max(0.0, end - start)
    if duration <= 0:
        return BoundaryScore(start, end, duration, -1e9, ("invalid_duration",))

    score = 0.0
    reasons: list[str] = []

    # Prefer a useful short-form duration, but never make duration dominate story quality.
    duration_delta = abs(duration - target_duration)
    score += max(0.0, 18.0 - duration_delta * 0.35)
    if duration >= 18.0:
        reasons.append("usable_duration")

    if segment_lookup is not None:
        segments = list(segment_lookup(start, end))
        text = " ".join(str(s.get("text", "")) for s in segments).strip()
        words = _word_count(text)
        if words >= 12:
            score += min(12.0, words / 12.0)
            reasons.append("complete_speech_window")
        if text.endswith((".", "!", "?", '"')):
            score += 7.0
            reasons.append("sentence_boundary")

    # Preserve editorial structure from the original candidate.
    original_duration = float(candidate.get("duration", 0.0))
    if original_duration > 0:
        drift = abs(duration - original_duration)
        score += max(0.0, 10.0 - drift * 0.5)
        if drift <= 2.0:
            reasons.append("minimal_boundary_drift")

    return BoundaryScore(start, end, duration, score, tuple(reasons))


def optimize_boundaries(
    candidate: dict[str, Any],
    *,
    segment_lookup: Callable[[float, float], Iterable[dict[str, Any]]] | None = None,
    search_radius: float = 8.0,
    step: float = 1.0,
    target_duration: float = 45.0,
) -> dict[str, Any]:
    """Search a small temporal neighborhood around a candidate.

    The optimizer is deliberately deterministic. A later AI critic can reject or
    refine its result, but media retrieval should never depend on an opaque model
    to establish valid boundaries.
    """
    original_start = float(candidate.get("start", 0.0))
    original_end = float(candidate.get("end", original_start))
    if original_end <= original_start:
        return {**candidate, "boundary_optimization": {"status": "invalid"}}

    offsets = []
    current = -search_radius
    while current <= search_radius + 1e-9:
        offsets.append(round(current, 3))
        current += step

    best: BoundaryScore | None = None
    for start_offset in offsets:
        for end_offset in offsets:
            start = max(0.0, original_start + start_offset)
            end = max(start, original_end + end_offset)
            scored = _boundary_score(
                candidate,
                start,
                end,
                target_duration=target_duration,
                segment_lookup=segment_lookup,
            )
            if best is None or scored.score > best.score:
                best = scored

    assert best is not None
    optimized = dict(candidate)
    optimized["start"] = best.start
    optimized["end"] = best.end
    optimized["duration"] = best.duration
    optimized["boundary_optimization"] = {
        "status": "optimized",
        "original_start": original_start,
        "original_end": original_end,
        "original_duration": original_end - original_start,
        "selected": best.to_dict(),
    }
    return optimized


def optimize_candidates(
    candidates: list[dict[str, Any]],
    *,
    segment_lookup: Callable[[float, float], Iterable[dict[str, Any]]] | None = None,
    limit: int = 50,
    search_radius: float = 8.0,
    step: float = 1.0,
) -> list[dict[str, Any]]:
    optimized = [
        optimize_boundaries(
            candidate,
            segment_lookup=segment_lookup,
            search_radius=search_radius,
            step=step,
        )
        for candidate in candidates[:limit]
    ]
    return optimized
