from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re


@dataclass(frozen=True)
class NarrativeSignals:
    question: float = 0.0
    answer: float = 0.0
    revelation: float = 0.0
    tension: float = 0.0
    payoff: float = 0.0
    emotional: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {k: round(float(v), 3) for k, v in self.__dict__.items()}


QUESTION_RE = re.compile(r"\?|\b(why|how|what|when|where|who|which|is it|can you|could you|would you)\b", re.I)
_REVELATION_RE = re.compile(r"\b(actually|turns out|the truth is|in fact|what happened was|i realized|we discovered|the reason is)\b", re.I)
_PAYOFF_RE = re.compile(r"\b(so that means|which means|therefore|that's why|the answer is|finally|in the end|and that's)\b", re.I)
_TENSION_RE = re.compile(r"\b(but|however|except|until|problem|mistake|failed|wrong|never|couldn't|didn't|lost|risk|danger)\b", re.I)


def _words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.casefold())


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _keyword_signal(text: str, pattern: re.Pattern[str]) -> float:
    return 1.0 if pattern.search(text) else 0.0


def narrative_signals(segments: list[dict[str, Any]]) -> NarrativeSignals:
    text = " ".join(str(s.get("text", "")) for s in segments).strip()
    if not text:
        return NarrativeSignals()
    density = min(1.0, len(_words(text)) / 110.0)
    question = _keyword_signal(text, QUESTION_RE)
    revelation = _keyword_signal(text, _REVELATION_RE)
    tension = _keyword_signal(text, _TENSION_RE)
    payoff = _keyword_signal(text, _PAYOFF_RE)
    answer = 1.0 if question and len(segments) >= 3 and density > 0.25 else 0.0
    emotional = _clamp((tension + revelation + payoff) / 3.0)
    return NarrativeSignals(question, answer, revelation, tension, payoff, emotional)


def _candidate(i: int, j: int, segments: list[dict[str, Any]], strategy: str) -> dict[str, Any] | None:
    start = float(segments[i].get("start", 0.0))
    end = float(segments[j].get("end", start))
    duration = end - start
    if duration < 18.0 or duration > 70.0:
        return None
    text = " ".join(str(s.get("text", "")).strip() for s in segments[i : j + 1]).strip()
    if len(_words(text)) < 12:
        return None
    signals = narrative_signals(segments[i : j + 1])
    return {
        "id": f"v6-{strategy}-{i:04d}-{j:04d}",
        "start": start,
        "end": end,
        "duration": duration,
        "text": text,
        "segment_ids": list(range(i, j + 1)),
        "generation_strategy": strategy,
        "narrative": signals.to_dict(),
        "editorial": {"semantic": {
            "payoff_strength": signals.payoff,
            "context_completeness": min(1.0, 0.45 + signals.answer * 0.3 + density_bonus(text)),
            "standalone_quality": min(1.0, 0.45 + signals.emotional * 0.25 + density_bonus(text)),
            "specificity": min(1.0, 0.35 + min(0.65, len(set(_words(text))) / 120.0)),
            "novelty_proxy": min(1.0, 0.35 + signals.revelation * 0.4 + signals.tension * 0.2),
            "topic_coherence": 0.75,
        }},
    }


def density_bonus(text: str) -> float:
    return min(0.3, len(_words(text)) / 300.0)


def generate_candidates(segments: list[dict[str, Any]], max_candidates: int = 1200) -> list[dict[str, Any]]:
    """Generate overlapping candidates using multiple editorial hypotheses.

    This deliberately over-generates. Ranking and the later editorial judge decide what survives.
    """
    if not segments:
        return []
    result: dict[str, dict[str, Any]] = {}
    strategies = {
        "narrative": (2, 18),
        "temporal": (1, 18),
        "semantic": (3, 14),
    }
    priority = {"narrative": 3, "semantic": 2, "temporal": 1}
    for strategy, (step, span) in strategies.items():
        for i in range(0, len(segments), step):
            for j in range(i, min(len(segments), i + span)):
                item = _candidate(i, j, segments, strategy)
                if item is None:
                    continue
                key = f"{round(item['start'], 3)}:{round(item['end'], 3)}"
                existing = result.get(key)
                if existing is None:
                    result[key] = item
                else:
                    item_strength = sum(item["narrative"].values())
                    existing_strength = sum(existing["narrative"].values())
                    if item_strength > existing_strength or (
                        item_strength == existing_strength
                        and priority.get(strategy, 0) > priority.get(existing.get("generation_strategy", ""), 0)
                    ):
                        result[key] = item
                if len(result) >= max_candidates:
                    break
            if len(result) >= max_candidates:
                break
        if len(result) >= max_candidates:
            break
    candidates = list(result.values())
    candidates.sort(key=lambda x: (
        x["narrative"].get("payoff", 0.0) + x["narrative"].get("tension", 0.0) + x["narrative"].get("revelation", 0.0),
        -abs(float(x["duration"]) - 45.0),
    ), reverse=True)
    return candidates
