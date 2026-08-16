from __future__ import annotations

from dataclasses import dataclass
from math import exp
import os
from typing import Any

from analysis_world import AnalysisWorld
from editorial_intelligence import narrative_signals
from editorial_reasoning import normalize_intent, reason_candidates
from ai_editorial import build_candidate_packet
from ai_provider import evaluate_ai


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
    narrative_tension: float
    narrative_revelation: float
    narrative_payoff: float
    confidence: float
    total: float

    def to_dict(self) -> dict[str, float]:
        return {k: round(float(v), 3) for k, v in self.__dict__.items()}


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


def _confidence(*, candidate: dict[str, Any], narrative: dict[str, float], audio: dict[str, float]) -> float:
    evidence = 0.35
    if candidate.get("text"):
        evidence += 0.2
    if candidate.get("scores"):
        evidence += 0.15
    if audio:
        evidence += 0.15
    narrative_strength = sum(narrative.values()) / max(1, len(narrative))
    evidence += 0.15 * narrative_strength
    return round(max(0.0, min(1.0, evidence)), 3)


def rank_candidate(candidate: dict[str, Any], *, target_duration: float = 45.0, scene_boundaries: list[dict[str, Any]] | None = None, selected: list[dict[str, Any]] | None = None, audio: dict[str, float] | None = None) -> EditorialSignals:
    selected = selected or []
    scores = candidate.get("scores") or {}
    semantic = candidate.get("editorial", {}).get("semantic") or {}
    audio = audio or {}
    narrative = narrative_signals([{"text": candidate.get("text", ""), "start": candidate.get("start", 0.0), "end": candidate.get("end", 0.0)}]).to_dict()

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

    narrative_tension = _clamp(narrative.get("tension", 0.0) * 100.0)
    narrative_revelation = _clamp(narrative.get("revelation", 0.0) * 100.0)
    narrative_payoff = _clamp(narrative.get("payoff", 0.0) * 100.0)

    total = (
        0.16 * hook + 0.13 * payoff + 0.10 * context + 0.10 * standalone
        + 0.06 * specificity + 0.05 * novelty + 0.05 * coherence + 0.05 * pacing
        + 0.04 * boundary + 0.05 * diversity + 0.05 * audio_rhythm
        + 0.025 * speech_density + 0.015 * audio_clarity
        + 0.04 * narrative_tension + 0.03 * narrative_revelation
        + 0.04 * narrative_payoff - 0.05 * repetition_penalty
    )
    confidence = _confidence(candidate=candidate, narrative=narrative, audio=audio)
    return EditorialSignals(
        hook=hook, payoff=payoff, context=context, standalone=standalone,
        specificity=specificity, novelty=novelty, coherence=coherence,
        pacing=pacing, boundary_alignment=boundary, diversity=diversity,
        repetition_penalty=repetition_penalty, audio_rhythm=audio_rhythm,
        speech_density=speech_density, audio_clarity=audio_clarity,
        narrative_tension=narrative_tension, narrative_revelation=narrative_revelation,
        narrative_payoff=narrative_payoff, confidence=confidence,
        total=_clamp(total),
    )


def _ai_rejudge(candidate: dict[str, Any], *, transcript: Any = None, audio: Any = None, vision: Any = None) -> dict[str, Any]:
    decision = evaluate_ai(build_candidate_packet(candidate, transcript=transcript, audio=audio, vision=vision))
    item = dict(candidate)
    item["ai_editorial"] = decision.to_dict()
    scores = decision.scores
    useful = [float(scores.get(key, 0.0)) for key in ("hook", "context", "tension", "payoff", "retention", "novelty", "shareability") if key in scores]
    ai_score = (sum(useful) / len(useful)) if useful else 0.0
    item["ai_editorial_score"] = round(ai_score, 6)
    item["ai_rejudge_active"] = decision.confidence > 0.0 and bool(useful)
    return item


def rank_candidates(candidates: list[dict[str, Any]], *, target_duration: float = 45.0, scene_boundaries: list[dict[str, Any]] | None = None, audio_profiles: dict[str, dict[str, float]] | None = None) -> list[dict[str, Any]]:
    audio_profiles = audio_profiles or {}
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        signals = rank_candidate(candidate, target_duration=target_duration, scene_boundaries=scene_boundaries, audio=audio_profiles.get(candidate.get("id", "")))
        item = dict(candidate)
        item["score"] = round(signals.total / 100.0, 6)
        item["editorial_score"] = round(signals.total / 100.0, 6)
        item["editorial_rank"] = round(signals.total, 2)
        item["editorial_signals"] = signals.to_dict()
        ranked.append(item)
    return sorted(ranked, key=lambda item: float(item.get("editorial_score", 0.0)), reverse=True)


def select_diverse(candidates: list[dict[str, Any]], *, limit: int = 10, target_duration: float = 45.0, scene_boundaries: list[dict[str, Any]] | None = None, audio_profiles: dict[str, dict[str, float]] | None = None, transcript: Any = None, vision: Any = None) -> list[dict[str, Any]]:
    remaining = [dict(item) for item in candidates]
    selected: list[dict[str, Any]] = []
    audio_profiles = audio_profiles or {}
    ai_top_k = max(0, min(20, int(os.getenv("NEXUX_AI_REVIEW_TOPK", "8"))))
    while remaining and len(selected) < limit:
        ranked = []
        for candidate in remaining:
            signals = rank_candidate(candidate, target_duration=target_duration, scene_boundaries=scene_boundaries, selected=selected, audio=audio_profiles.get(candidate.get("id", "")))
            local_score = signals.total
            ranked.append((local_score, signals, candidate))
        ranked.sort(key=lambda item: item[0] * (0.85 + 0.15 * item[1].confidence), reverse=True)
        shortlist = ranked[:ai_top_k] if ai_top_k else ranked[:1]
        ai_items: list[tuple[float, EditorialSignals, dict[str, Any]]] = []
        for local_score, signals, candidate in shortlist:
            judged = _ai_rejudge(candidate, transcript=transcript, audio=audio_profiles.get(candidate.get("id", "")), vision=vision)
            ai_score = float(judged.get("ai_editorial_score", 0.0)) * 100.0
            verdict = judged.get("ai_editorial", {}).get("verdict")
            combined = local_score
            if judged.get("ai_rejudge_active"):
                combined = 0.72 * local_score + 0.28 * ai_score
                if verdict == "REJECT":
                    combined -= 12.0
                elif verdict == "KEEP":
                    combined += 4.0
                elif verdict == "REFINE":
                    combined += 1.5
            ai_items.append((combined, signals, judged))
        _, signals, winner = max(ai_items, key=lambda item: item[0] * (0.85 + 0.15 * item[1].confidence))
        chosen = dict(winner)
        chosen["editorial_rank"] = round(signals.total, 2)
        chosen["editorial_signals"] = signals.to_dict()
        chosen["editorial_evidence"] = {
            "narrative": {
                "tension": round(signals.narrative_tension / 100.0, 3),
                "revelation": round(signals.narrative_revelation / 100.0, 3),
                "payoff": round(signals.narrative_payoff / 100.0, 3),
            },
            "confidence": signals.confidence,
            "generation_strategy": chosen.get("generation_strategy", "legacy_temporal"),
            "ai_rejudge_active": bool(chosen.get("ai_rejudge_active")),
        }
        selected.append(chosen)
        remaining.remove(next(item[2] for item in ai_items if item[2].get("id") == chosen.get("id")))
    return selected


def select_diverse_from_world(world: AnalysisWorld, *, limit: int = 10, target_duration: float = 45.0) -> list[dict[str, Any]]:
    """Authoritative editorial selection driven by one AnalysisWorld and its explicit intent."""
    world.validate()
    raw_candidates = [dict(item) for item in world.candidates]
    intent_payload = dict(world.editorial.get("intent", {}) or {})
    if not intent_payload:
        intent_payload = {
            "objective": str(world.editorial.get("genre", "find_best_clips") or "find_best_clips"),
            "target_duration": float(world.editorial.get("target_duration", target_duration) or target_duration),
            "limit": limit,
        }
    intent = normalize_intent(intent_payload)
    reasoned = reason_candidates(raw_candidates, intent=intent)
    # Intent is a first-class narrowing signal: keep a bounded evidence set before
    # multimodal ranking/AI rejudge, while preserving all evidence in the World.
    shortlist_size = max(limit * 4, min(40, len(reasoned)))
    candidates = reasoned[:shortlist_size]
    effective_duration = float(intent.target_duration or target_duration)
    audio_profiles = dict(world.audio.get("profiles", {}) or {})
    scenes = list(world.vision.get("scenes", []) or [])
    transcript = world.transcript
    vision = dict(world.vision)
    selected = select_diverse(
        candidates,
        limit=min(limit, intent.limit),
        target_duration=effective_duration,
        scene_boundaries=scenes,
        audio_profiles={key: dict(value) for key, value in audio_profiles.items()},
        transcript=transcript,
        vision=vision,
    )
    for item in selected:
        item["analysis_world"] = {
            "schema_version": world.schema_version,
            "job_id": world.job_id,
            "modalities": sorted(world.modalities),
            "confidence": dict(world.confidence),
            "provenance": dict(world.provenance),
        }
        item["editorial_intent"] = intent.to_dict()
        item["editorial_reasoning"] = item.get("intent_reasoning", {})
    return selected
