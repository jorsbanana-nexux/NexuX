from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EditorialIntent:
    """Explicit user/editorial objective used by ranking and reasoning."""

    objective: str = "find_best_clips"
    audience: str = "general"
    platform: str = "generic"
    tone: str = "natural"
    style: str = "balanced"
    target_duration: float = 45.0
    limit: int = 10
    required_topics: tuple[str, ...] = ()
    excluded_topics: tuple[str, ...] = ()
    preferences: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_topics"] = list(self.required_topics)
        payload["excluded_topics"] = list(self.excluded_topics)
        return payload

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "EditorialIntent":
        value = dict(value or {})
        return cls(
            objective=str(value.get("objective", "find_best_clips")),
            audience=str(value.get("audience", "general")),
            platform=str(value.get("platform", "generic")),
            tone=str(value.get("tone", "natural")),
            style=str(value.get("style", "balanced")),
            target_duration=float(value.get("target_duration", 45.0)),
            limit=max(1, int(value.get("limit", 10))),
            required_topics=tuple(str(x) for x in value.get("required_topics", []) or []),
            excluded_topics=tuple(str(x) for x in value.get("excluded_topics", []) or []),
            preferences={str(k): float(v) for k, v in (value.get("preferences", {}) or {}).items()},
        )


def normalize_intent(value: EditorialIntent | dict[str, Any] | None) -> EditorialIntent:
    if isinstance(value, EditorialIntent):
        return value
    return EditorialIntent.from_dict(value)
