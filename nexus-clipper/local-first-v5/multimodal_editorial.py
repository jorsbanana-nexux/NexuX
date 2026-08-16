from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Any


GENRE_RULES = {
    "podcast": {"words": {"podcast", "episode", "guest", "host", "interview"}, "weights": {"hook": 1.2, "context": 1.15, "payoff": 1.1}},
    "gaming": {"words": {"game", "gaming", "match", "boss", "ranked", "win", "lose", "stream"}, "weights": {"hook": 1.25, "pacing": 1.2, "reaction": 1.25}},
    "education": {"words": {"learn", "lesson", "explain", "explained", "science", "history", "study"}, "weights": {"context": 1.3, "specificity": 1.2, "payoff": 1.15}},
    "news": {"words": {"breaking", "news", "report", "latest", "update", "president", "election"}, "weights": {"novelty": 1.25, "clarity": 1.2, "context": 1.15}},
    "vlog": {"words": {"today", "day", "morning", "trip", "travel", "vlog", "life"}, "weights": {"emotion": 1.2, "visual": 1.2, "pacing": 1.1}},
    "comedy": {"words": {"funny", "joke", "laugh", "comedy", "haha", "ridiculous"}, "weights": {"reaction": 1.35, "pacing": 1.25, "hook": 1.15}},
}


@dataclass(frozen=True)
class EditorialDecision:
    genre: str
    prompt_terms: list[str]
    candidate_bias: dict[str, float]
    virality_score: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[\w']+", text.casefold()) if len(w) > 2}


def detect_genre(text: str, requested: str | None = None) -> tuple[str, float]:
    if requested and requested != "auto":
        return requested, 1.0
    tokens = _words(text)
    best = ("general", 0.35)
    for genre, rule in GENRE_RULES.items():
        overlap = len(tokens & rule["words"])
        score = overlap / max(3.0, len(rule["words"]) ** 0.5)
        if score > best[1]:
            best = (genre, min(1.0, score))
    return best


def parse_prompt(prompt: str | None) -> list[str]:
    if not prompt:
        return []
    stop = {"the", "and", "for", "with", "from", "that", "this", "into", "make", "clip", "clips", "video"}
    return [w for w in re.findall(r"[\w']+", prompt.casefold()) if len(w) >= 3 and w not in stop][:18]


def prompt_relevance(candidate: dict[str, Any], terms: list[str]) -> float:
    if not terms:
        return 0.0
    text = str(candidate.get("text", "")).casefold()
    hits = sum(1 for term in terms if term in text)
    return min(100.0, 100.0 * hits / max(1, len(terms)))


def _signals(candidate: dict[str, Any]) -> dict[str, float]:
    s = candidate.get("editorial_signals") or candidate.get("scores") or {}
    return {
        "hook": float(s.get("hook", 0.0)),
        "payoff": float(s.get("payoff", s.get("payoff_strength", 0.0))),
        "context": float(s.get("context", s.get("context_completeness", 0.0))),
        "standalone": float(s.get("standalone", s.get("standalone_quality", 0.0))),
        "pacing": float(s.get("pacing", 0.0)),
        "novelty": float(s.get("novelty", s.get("novelty_proxy", 0.0))),
        "emotion": float(s.get("narrative_tension", 0.0)),
        "reaction": float(s.get("audio_rhythm", 0.0)),
        "specificity": float(s.get("specificity", 0.0)),
        "clarity": float(s.get("audio_clarity", 0.0)),
        "visual": float(s.get("boundary_alignment", 0.0)),
    }


def score_virality(candidate: dict[str, Any], *, prompt_terms: list[str], genre: str) -> float:
    s = _signals(candidate)
    prompt = prompt_relevance(candidate, prompt_terms)
    base = (
        0.20 * s["hook"] + 0.16 * s["payoff"] + 0.10 * s["standalone"] +
        0.10 * s["novelty"] + 0.10 * s["pacing"] + 0.08 * s["emotion"] +
        0.08 * s["reaction"] + 0.06 * s["specificity"] + 0.05 * s["clarity"] +
        0.07 * s["visual"]
    )
    if prompt_terms:
        base = 0.82 * base + 0.18 * prompt
    rule = GENRE_RULES.get(genre, {})
    weights = rule.get("weights", {})
    bonus = 0.0
    if weights:
        bonus = sum(min(1.25, weights.get(k, 1.0)) * s.get(k, 0.0) for k in weights) / max(1, len(weights)) * 8.0
    return round(max(0.0, min(100.0, base + bonus)), 2)


def apply_editorial_intelligence(candidates: list[dict[str, Any]], *, prompt: str | None, genre: str | None) -> tuple[list[dict[str, Any]], EditorialDecision]:
    all_text = " ".join(str(c.get("text", "")) for c in candidates)
    detected, confidence = detect_genre(all_text, genre)
    terms = parse_prompt(prompt)
    bias = GENRE_RULES.get(detected, {}).get("weights", {})
    enriched = []
    for candidate in candidates:
        item = dict(candidate)
        item["prompt_relevance"] = round(prompt_relevance(item, terms), 2)
        item["virality_score"] = score_virality(item, prompt_terms=terms, genre=detected)
        item["genre"] = detected
        item["editorial_rank"] = round(0.72 * float(item.get("editorial_rank", 0.0)) + 0.28 * item["virality_score"], 2)
        enriched.append(item)
    enriched.sort(key=lambda c: float(c.get("editorial_rank", 0.0)), reverse=True)
    decision = EditorialDecision(detected, terms, dict(bias), max((float(c.get("virality_score", 0)) for c in enriched), default=0.0), confidence)
    return enriched, decision


def detect_filler_segments(segments: list[dict[str, Any]], *, min_pause: float = 0.42) -> list[dict[str, Any]]:
    filler = re.compile(r"\b(um+|uh+|er+|like|you know|sort of|kind of|basically|actually)\b", re.I)
    cuts: list[dict[str, Any]] = []
    for seg in segments:
        text = str(seg.get("text", ""))
        if filler.search(text):
            cuts.append({"start": float(seg.get("start", 0.0)), "end": float(seg.get("end", 0.0)), "reason": "filler"})
    for a, b in zip(segments, segments[1:]):
        pause = float(b.get("start", 0.0)) - float(a.get("end", 0.0))
        if pause >= min_pause:
            cuts.append({"start": float(a.get("end", 0.0)), "end": float(b.get("start", 0.0)), "reason": "pause"})
    return cuts


def apply_cleanup_to_candidate(candidate: dict[str, Any], cuts: list[dict[str, Any]]) -> dict[str, Any]:
    start, end = float(candidate["start"]), float(candidate["end"])
    relevant = [c for c in cuts if c["end"] > start and c["start"] < end]
    removed = sum(max(0.0, min(end, c["end"]) - max(start, c["start"])) for c in relevant)
    item = dict(candidate)
    item["cleanup"] = {"cuts": relevant, "removed_seconds": round(removed, 3), "enabled": bool(relevant)}
    item["effective_duration"] = round(max(0.0, float(candidate.get("duration", end - start)) - removed), 3)
    return item


def dynamic_layout_plan(*, aspect_ratio: str, genre: str, face_tracking: bool, auto_zoom: bool) -> dict[str, Any]:
    safe = {"9:16": {"anchor":"center", "headroom":0.16}, "1:1": {"anchor":"center", "headroom":0.12}, "16:9": {"anchor":"center", "headroom":0.08}}.get(aspect_ratio, {"anchor":"center", "headroom":0.12})
    style = "talking_head" if genre in {"podcast", "news", "education"} else "kinetic" if genre in {"gaming", "comedy"} else "balanced"
    return {"aspect_ratio": aspect_ratio, "genre": genre, "layout": style, "anchor": safe["anchor"], "headroom": safe["headroom"], "face_tracking": face_tracking, "auto_zoom": auto_zoom}


def critic(render_meta: list[dict[str, Any]], *, requested_duration: float, expected_aspect: str) -> dict[str, Any]:
    issues: list[str] = []
    scores: list[float] = []
    for item in render_meta:
        q = item.get("quality") or {}
        if q.get("verdict") != "APPROVED":
            issues.append(f"{item.get('clip_id','clip')}: render quality not approved")
        dims = item.get("output_dimensions") or {}
        if expected_aspect == "9:16" and dims.get("height",0) <= dims.get("width",0):
            issues.append(f"{item.get('clip_id','clip')}: expected vertical composition")
        scores.append(float((q.get("score") or 0.0) if isinstance(q, dict) else 0.0))
    score = round(sum(scores) / max(1, len(scores)), 2)
    return {"score": score, "issues": issues, "revision_required": bool(issues), "requested_duration": requested_duration, "expected_aspect": expected_aspect}


def revision_actions(critique: dict[str, Any]) -> list[str]:
    if not critique.get("revision_required"):
        return []
    actions = []
    if any("vertical" in issue for issue in critique.get("issues", [])):
        actions.append("re-render-aspect")
    if any("quality" in issue for issue in critique.get("issues", [])):
        actions.append("re-render-quality")
    return actions
