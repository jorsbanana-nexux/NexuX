from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EditorialDecision:
    verdict: str
    confidence: float
    scores: dict[str, float]
    adjustments: dict[str, float]
    evidence: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "scores": self.scores,
            "adjustments": self.adjustments,
            "evidence": list(self.evidence),
            "summary": self.summary,
        }


class EditorialProvider(Protocol):
    def evaluate(self, packet: dict[str, Any]) -> dict[str, Any]: ...


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_decision(payload: dict[str, Any]) -> EditorialDecision:
    verdict = str(payload.get("verdict", "REVIEW")).upper()
    if verdict not in {"KEEP", "REFINE", "REJECT", "REVIEW"}:
        verdict = "REVIEW"

    confidence = max(0.0, min(1.0, _number(payload.get("confidence"))))
    raw_scores = payload.get("scores") or {}
    scores = {
        str(k): max(0.0, min(1.0, _number(v) / 100.0 if _number(v) > 1 else _number(v)))
        for k, v in raw_scores.items()
    }
    raw_adjustments = payload.get("adjustments") or {}
    adjustments = {
        "start": max(-15.0, min(15.0, _number(raw_adjustments.get("start")))),
        "end": max(-15.0, min(15.0, _number(raw_adjustments.get("end")))),
    }
    evidence = tuple(str(x) for x in (payload.get("evidence") or [])[:8])
    summary = str(payload.get("summary", ""))[:1000]
    return EditorialDecision(verdict, confidence, scores, adjustments, evidence, summary)


class NullEditorialProvider:
    """Safe offline fallback: never calls a remote model."""

    def evaluate(self, packet: dict[str, Any]) -> dict[str, Any]:
        return {
            "verdict": "REVIEW",
            "confidence": 0.0,
            "scores": {},
            "adjustments": {"start": 0.0, "end": 0.0},
            "evidence": ["no_ai_provider_configured"],
            "summary": "AI editorial provider is not configured; local engine remains authoritative.",
        }


def build_candidate_packet(candidate: dict[str, Any], *, transcript: Any = None, audio: Any = None, vision: Any = None) -> dict[str, Any]:
    """Create a bounded, provider-neutral packet; never expose filesystem secrets."""
    return {
        "candidate": candidate,
        "transcript": transcript,
        "audio": audio,
        "vision": vision,
        "schema_version": "nexux.editorial.v1",
    }


def evaluate_with_provider(provider: EditorialProvider | None, packet: dict[str, Any]) -> EditorialDecision:
    active = provider or NullEditorialProvider()
    try:
        raw = active.evaluate(packet)
        if not isinstance(raw, dict):
            raise ValueError("provider response must be an object")
        return validate_decision(raw)
    except Exception as exc:
        return validate_decision({
            "verdict": "REVIEW",
            "confidence": 0.0,
            "evidence": [f"provider_failure:{type(exc).__name__}"],
            "summary": "AI provider failed validation; local editorial pipeline remains authoritative.",
        })
