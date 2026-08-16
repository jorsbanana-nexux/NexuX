from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from narrative_model import _clamp, _overlap

SCHEMA_VERSION = "1.0"

@dataclass(frozen=True)
class ContextWindow:
    role: str
    start: float
    end: float
    text: str
    distance: float
    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "start": round(self.start, 3), "end": round(self.end, 3), "text": self.text, "distance": round(self.distance, 3)}

@dataclass(frozen=True)
class ContextualNarrativeAssessment:
    schema_version: str
    candidate_id: str
    before: tuple[ContextWindow, ...]
    candidate: ContextWindow
    after: tuple[ContextWindow, ...]
    promise_text: str
    payoff_text: str
    promise_payoff_match: float
    context_gain: float
    dependency_score: float
    context_integrity: float
    premature_cut_risk: float
    unresolved_question_risk: float
    recommendation: str
    confidence: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "before": [x.to_dict() for x in self.before],
            "candidate": self.candidate.to_dict(),
            "after": [x.to_dict() for x in self.after],
            "promise_text": self.promise_text,
            "payoff_text": self.payoff_text,
            "promise_payoff_match": round(self.promise_payoff_match, 3),
            "context_gain": round(self.context_gain, 3),
            "dependency_score": round(self.dependency_score, 3),
            "context_integrity": round(self.context_integrity, 3),
            "premature_cut_risk": round(self.premature_cut_risk, 3),
            "unresolved_question_risk": round(self.unresolved_question_risk, 3),
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 3),
            "reasons": list(self.reasons),
        }

_Q = re.compile(r"\?|\b(why|how|what|when|where|who|which|can|could|would|should)\b", re.I)
_RESOLUTION = re.compile(r"\b(so|therefore|which means|that's why|as a result|finally|in the end|because|resulted in|after that)\b", re.I)


def _segment_windows(transcript: Mapping[str, Any], candidate: Mapping[str, Any], radius: float = 18.0) -> tuple[list[ContextWindow], ContextWindow, list[ContextWindow]]:
    start = float(candidate.get("start", 0.0)); end = float(candidate.get("end", start))
    before: list[ContextWindow] = []; after: list[ContextWindow] = []; inside: list[ContextWindow] = []
    for seg in transcript.get("segments", []) or []:
        s = float(seg.get("start", 0.0)); e = float(seg.get("end", s)); text = str(seg.get("text", "")).strip()
        if not text or e < start - radius or s > end + radius: continue
        if e <= start:
            before.append(ContextWindow("before", s, e, text, max(0.0, start - e)))
        elif s >= end:
            after.append(ContextWindow("after", s, e, text, max(0.0, s - end)))
        else:
            inside.append(ContextWindow("candidate", s, e, text, 0.0))
    if inside:
        candidate_window = ContextWindow("candidate", min(x.start for x in inside), max(x.end for x in inside), " ".join(x.text for x in inside), 0.0)
    else:
        candidate_window = ContextWindow("candidate", start, end, str(candidate.get("text", "")), 0.0)
    return before[-8:], candidate_window, after[:8]


def verify_context(candidate: Mapping[str, Any], transcript: Mapping[str, Any] | None = None, *, radius: float = 18.0) -> ContextualNarrativeAssessment:
    transcript = transcript or {}
    before, candidate_window, after = _segment_windows(transcript, candidate, radius)
    ctext = candidate_window.text
    before_text = " ".join(x.text for x in before)
    after_text = " ".join(x.text for x in after)

    promise = before_text if _Q.search(ctext[:240]) else ""
    payoff_candidates = [x.text for x in after if _RESOLUTION.search(x.text)]
    payoff = payoff_candidates[0] if payoff_candidates else (after[-1].text if after else "")
    promise_payoff_match = _overlap(promise or ctext, payoff) if payoff else 0.0
    dependency = _clamp((0.55 if before and (_Q.search(before[-1].text) or _RESOLUTION.search(before[-1].text)) else 0.0) + 0.45 * (1.0 - min(1.0, len(ctext.split()) / 120.0)))
    context_gain = _clamp(0.5 * (len(before) / 8.0) + 0.5 * (len(after) / 8.0))
    context_integrity = _clamp(0.55 + 0.25 * context_gain + 0.20 * promise_payoff_match)
    unresolved = _clamp((0.65 if _Q.search(ctext) and not payoff_candidates else 0.0) + 0.25 * (1.0 - promise_payoff_match))
    premature = _clamp(0.55 * unresolved + 0.25 * dependency + 0.20 * (1.0 - context_integrity))
    if promise_payoff_match >= 0.55 and context_integrity >= 0.72 and premature < 0.45:
        recommendation = "KEEP"
    elif context_integrity >= 0.55:
        recommendation = "EXTEND" if payoff else "REFINE"
    else:
        recommendation = "REVIEW"
    reasons: list[str] = []
    if payoff_candidates: reasons.append("found post-candidate resolution evidence")
    if promise_payoff_match >= 0.55: reasons.append("opening promise is semantically connected to later payoff")
    if dependency >= 0.55: reasons.append("candidate depends on nearby context")
    if premature >= 0.45: reasons.append("candidate may end before the narrative resolves")
    confidence = _clamp(0.45 + 0.08 * min(5, len(before) + len(after)) + (0.15 if transcript.get("segments") else 0.0) + (0.10 if payoff else 0.0))
    return ContextualNarrativeAssessment(SCHEMA_VERSION, str(candidate.get("id", "")), tuple(before), candidate_window, tuple(after), promise, payoff, promise_payoff_match, context_gain, dependency, context_integrity, premature, unresolved, recommendation, confidence, tuple(reasons))
