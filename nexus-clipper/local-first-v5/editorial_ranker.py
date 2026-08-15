from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Any


@dataclass(frozen=True)
class EditorialSignals:
    hook: float
    payoff: float
    context: float
    standalone: float
    specificity: float
    novelty: float
    coherence: float
    pacing: float
    boundary_alignment: float
    diversity: float
    repetition_penalty: float
    audio_rhythm: float
    speech_density: float
    audio_clarity: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return {k: round(v, 3) for k, v in self.__dict__.items()}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _duration_score(seconds: float, target: float = 45.0) -> float:
    return _clamp(100.0 * exp(-abs(seconds - target) / 28.0))


def _boundary_alignment(candidate: dict[str, Any], scene_boundaries: list[dict[str, Any]] | None) -> float:
    if not scene_boundaries:
        return 50.0
    start = float(candidate.get("start", 0.0))
    end = float(candidate.get("end", start))

    def near(value: float) -> float:
        distances = [abs(value - float(scene.get("start", value))) for scene in scene_boundaries]
        distances.extend(abs(value - float(scene.get("end", value))) for scene in scene_boundaries)
        return 100.0 * exp(-min(distances, default=5.0) / 2.5)

    return 0.5 * (near(start) + near(end))


def _repetition_penalty(candidate: dict[str, Any], selected: list[dict[str, Any]]) -> float:
    text = set(str(candidate.get("text", "")).casefold().split())
    if not text or not selected:
        return 0.0
    overlaps = []
    for item in selected:
        other = set(str(item.get("text", "")).casefold().split())
        if other:
            overlaps.append(len(text & other) / max(1, len(text | other)))
    return _clamp(max(overlaps, default=0.0) * 100.0)


def _diversity(candidate: dict[str, Any], selected: list[dict[str, Any]]) -> float:
    if not selected:
        return 100.0
    start = float(candidate.get("start", 0.0))
    nearest = min(abs(start - float(item.get("start", start))) for item in selected)
    return _clamp(100.0 * (1.0 - exp(-nearest / 15.0)))


def rank_candidate(candidate: dict[str, Any], *, target_duration: float = 45.0, scene_boundaries: list[dict[str, Any]] | None = None, selected: list[dict[str, Any]] | None = None, audio: dict[str, float] | None = None) -> EditorialSignals:
    selected = selected or []
    scores = candidate.get("scores") or {}
    semantic = candidate.get("editorial", {}).get("semantic") or {}
    audio = audio or {}

    hook = _clamp(float(scores.get("hook", 0.0)))
    payoff = _clamp(float(semantic.get("payoff_strength", 0.0)) * 100.0)
    context = _clamp(float(semantic.get("context_completeness", 0.0)) * 100.0)
    standalone = _clamp(float(semantic.get("standalone_quality", 0.0)) * 100.0)
    specificity = _clamp(float(semantic.get("specificity", 0.0)) * 100.0)
    novelty = _clamp(float(semantic.get("novelty_proxy", 0.0)) * 100.0)
    coherence = _clamp(float(semantic.get("topic_coherence", 0.0)) * 100.0)
    pacing = _duration_score(float(candidate.get("duration", 0.0)), target_duration)
    boundary = _boundary_alignment(candidate, scene_boundaries)
    repetition_penalty = _repetition_penalty(candidate, selected)
    diversity = _diversity(candidate, selected)

    audio_rhythm = _clamp(float(audio.get("rhythm", 50.0)))
    speech_density = _clamp(float(audio.get("speech_density", 50.0)))
    audio_clarity = _clamp(float(audio.get("clarity", 50.0)))

    total = (
        0.18 * hook + 0.14 * payoff + 0.11 * context + 0.11 * standalone
        + 0.07 * specificity + 0.06 * novelty + 0.06 * coherence + 0.06 * pacing
        + 0.05 * boundary + 0.05 * diversity + 0.06 * audio_rhythm
        + 0.03 * speech_density + 0.02 * audio_clarity - 0.05 * repetition_penalty
    )
    return EditorialSignals(
        hook=hook, payoff=payoff, context=context, standalone=standalone,
        specificity=specificity, novelty=novelty, coherence=coherence,
        pacing=pacing, boundary_alignment=boundary, diversity=diversity,
        repetition_penalty=repetition_penalty, audio_rhythm=audio_rhythm,
        speech_density=speech_density, audio_clarity=audio_clarity,
        total=_clamp(total),
    )


def select_diverse(candidates: list[dict[str, Any]], *, limit: int = 10, target_duration: float = 45.0, scene_boundaries: list[dict[str, Any]] | None = None, audio_profiles: dict[str, dict[str, float]] | None = None) -> list[dict[str, Any]]:
    remaining = [dict(item) for item in candidates]
    selected: list[dict[str, Any]] = []
    audio_profiles = audio_profiles or {}
    while remaining and len(selected) < limit:
        ranked = []
        for candidate in remaining:
            signals = rank_candidate(candidate, target_duration=target_duration, scene_boundaries=scene_boundaries, selected=selected, audio=audio_profiles.get(candidate.get("id", "")))
            ranked.append((signals, candidate))
        signals, winner = max(ranked, key=lambda pair: pair[0].total)
        chosen = dict(winner)
        chosen["editorial_rank"] = round(signals.total, 2)
        chosen["editorial_signals"] = signals.to_dict()
        selected.append(chosen)
        remaining.remove(winner)
    return selected
