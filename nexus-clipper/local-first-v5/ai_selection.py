from __future__ import annotations

from typing import Any

from ai_editorial import evaluate_with_provider
from ai_prompt import build_editorial_prompt


def _score(candidate: dict[str, Any]) -> float:
    for key in ("editorial_rank", "score", "editorial_score"):
        value = candidate.get(key)
        if value is not None:
            try:
                n = float(value)
                return n / 100.0 if n > 1 else n
            except (TypeError, ValueError):
                pass
    return 0.0


def select_with_ai(candidates: list[dict[str, Any]], provider: Any | None = None) -> list[dict[str, Any]]:
    """Evaluate a bounded candidate pool and attach validated AI decisions.

    AI never executes edits and never becomes the sole source of truth. Local
    editorial score remains the deterministic fallback when AI is unavailable.
    """
    if not candidates:
        return []

    # Keep remote cost bounded. Candidate generation/ranking should have already
    # removed obvious low-quality candidates before this point.
    pool = sorted(candidates, key=_score, reverse=True)[:20]
    results: list[dict[str, Any]] = []
    for candidate in pool:
        packet = {
            "candidate": candidate,
            "schema_version": "nexux.editorial.v1",
        }
        decision = evaluate_with_provider(provider, packet)
        item = dict(candidate)
        item["ai_editorial"] = decision.to_dict()
        item["ai_verdict"] = decision.verdict
        item["ai_confidence"] = decision.confidence
        item["ai_score"] = sum(decision.scores.values()) / len(decision.scores) if decision.scores else 0.0
        results.append(item)

    # Deterministic tie-breaking: AI confidence + AI score first, local score
    # second. REJECT is kept in the result for auditability but ranked last.
    def final_key(item: dict[str, Any]) -> tuple[int, float, float]:
        reject = 0 if item.get("ai_verdict") == "REJECT" else 1
        combined = 0.65 * float(item.get("ai_score", 0.0)) + 0.35 * float(item.get("ai_confidence", 0.0))
        return reject, combined, _score(item)

    return sorted(results, key=final_key, reverse=True)
