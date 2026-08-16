from __future__ import annotations

from typing import Any, Mapping

from autonomous_edit_session import RevisionAction
from multimodal_editorial import revision_actions


def build_revision_actions(critique: Mapping[str, Any]) -> tuple[RevisionAction, ...]:
    raw = revision_actions(dict(critique))
    if not raw:
        return ()
    actions: list[RevisionAction] = []
    for index, item in enumerate(raw):
        if isinstance(item, str):
            actions.append(RevisionAction(action=item, priority=max(0.0, 1.0 - index * 0.05)))
            continue
        mapping = dict(item)
        actions.append(
            RevisionAction(
                action=str(mapping.get("action", mapping.get("type", "review"))),
                target=str(mapping.get("target", "")),
                reason=str(mapping.get("reason", "")),
                priority=float(mapping.get("priority", 1.0 - index * 0.05) or 0.0),
                parameters=dict(mapping.get("parameters", {}) or {}),
            )
        )
    return tuple(sorted(actions, key=lambda action: action.priority, reverse=True))


def apply_safe_revision_metadata(render: Mapping[str, Any], actions: tuple[RevisionAction, ...], attempt: int) -> dict[str, Any]:
    """Attach revision instructions without mutating source media or pretending a render occurred."""
    result = dict(render)
    result["revision"] = {
        "attempt": int(attempt),
        "actions": [action.to_dict() for action in actions],
        "media_mutated": False,
    }
    return result
