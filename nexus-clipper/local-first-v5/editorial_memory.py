from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import exp
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"

@dataclass(frozen=True)
class EditorialMemoryEvent:
    event_id: str
    user_id: str
    signal: str
    value: float
    context: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    source: str = "human"

    def normalized(self) -> "EditorialMemoryEvent":
        return EditorialMemoryEvent(self.event_id, self.user_id, self.signal, max(-1.0, min(1.0, float(self.value))), dict(self.context), self.created_at or datetime.now(timezone.utc).isoformat(), self.source)

@dataclass(frozen=True)
class EditorialPreferenceProfile:
    schema_version: str
    user_id: str
    weights: Mapping[str, float] = field(default_factory=dict)
    sample_count: int = 0
    confidence: float = 0.0
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "user_id": self.user_id, "weights": dict(self.weights), "sample_count": self.sample_count, "confidence": self.confidence, "updated_at": self.updated_at}

def _decay(age_days: float, half_life_days: float = 30.0) -> float:
    return exp(-max(0.0, age_days) / max(1.0, half_life_days))

def build_profile(events: list[EditorialMemoryEvent], *, now: datetime | None = None, prior: EditorialPreferenceProfile | None = None, learning_rate: float = 0.12) -> EditorialPreferenceProfile:
    now = now or datetime.now(timezone.utc)
    weights = dict(prior.weights) if prior else {}
    count = prior.sample_count if prior else 0
    user_id = prior.user_id if prior else (events[0].user_id if events else "")
    for raw in events:
        event = raw.normalized()
        try:
            created = datetime.fromisoformat(event.created_at.replace("Z", "+00:00"))
            age_days = (now - created).total_seconds() / 86400.0
        except ValueError:
            age_days = 0.0
        influence = learning_rate * _decay(age_days) * max(0.1, min(1.0, abs(event.value)))
        old = float(weights.get(event.signal, 0.0))
        direction = 1.0 if event.value > 0 else -1.0
        weights[event.signal] = max(-1.0, min(1.0, old + influence * direction))
        count += 1
    confidence = max(0.0, min(1.0, count / 20.0))
    return EditorialPreferenceProfile(SCHEMA_VERSION, user_id, weights, count, confidence, now.isoformat())

def personalized_adjustment(profile: EditorialPreferenceProfile, features: Mapping[str, float], *, max_adjustment: float = 0.15) -> float:
    if not profile.user_id or profile.confidence <= 0.0:
        return 0.0
    raw = sum(float(profile.weights.get(key, 0.0)) * float(value) for key, value in features.items())
    scale = min(max_adjustment, max_adjustment * profile.confidence)
    return max(-scale, min(scale, raw * scale))
