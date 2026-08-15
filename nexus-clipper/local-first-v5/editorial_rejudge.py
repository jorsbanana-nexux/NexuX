from __future__ import annotations

from typing import Any, Callable

from editorial_critic import apply_critique, critique_candidate
from editorial_ranker import rank_candidates


def _score(candidate: dict[str, Any]) -> float:
    value = candidate.get("score", candidate.get("editorial_score", 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rejudge_candidate(
    candidate: dict[str, Any],
    *,
    ranker: Callable[[list[dict[str, Any]]], list[Any]] | None = None,
) -> dict[str, Any]:
    """Critique, refine, and compare a candidate against its original form.

    The original is never discarded until the refined version has been
    re-ranked. If refinement does not improve the editorial score, the
    original is retained.
    """
    original = dict(candidate)
    critique = critique_candidate(original)
    if critique.verdict == "KEEP":
        original["rejudge"] = {"selected": "original", "critic": critique.to_dict()}
        return original

    refined = apply_critique(original, critique)
    rank = ranker or rank_candidates
    try:
        ranked = rank([refined])
        if ranked:
            item = ranked[0]
            refined = item.model_dump() if hasattr(item, "model_dump") else item.dict() if hasattr(item, "dict") else dict(item)
    except Exception:
        refined["rejudge_error"] = "ranking_failed"

    original_score = _score(original)
    refined_score = _score(refined)
    selected = "refined" if refined_score > original_score else "original"
    winner = refined if selected == "refined" else original
    winner["rejudge"] = {
        "selected": selected,
        "original_score": original_score,
        "refined_score": refined_score,
        "critic": critique.to_dict(),
    }
    return winner


def rejudge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refined = [rejudge_candidate(candidate) for candidate in candidates]
    refined.sort(key=_score, reverse=True)
    return refined
