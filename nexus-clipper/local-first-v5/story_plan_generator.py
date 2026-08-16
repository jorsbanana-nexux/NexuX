from __future__ import annotations

from typing import Any
from story_plan import StoryPlan, StoryPlanSequence, StoryPlanDecision, build_story_plan


def _item_id(item: dict[str, Any], fallback: str) -> str:
    return str(item.get("id") or fallback)


def generate_story_plans(candidates: list[dict[str, Any]], *, objective: str = "find_best_clips", audience: str = "general", platform: str = "short_form", target_duration: float = 45.0, max_plans: int = 5) -> list[StoryPlan]:
    if not candidates:
        return []
    ranked = sorted(candidates, key=lambda x: float(x.get("score", x.get("editorial_score", 0.0)) or 0.0), reverse=True)
    plans: list[StoryPlan] = []
    templates = [
        ("hook_first", ["opening", "setup", "core", "revelation", "payoff", "ending"]),
        ("context_first", ["setup", "opening", "core", "revelation", "payoff", "ending"]),
        ("result_first", ["payoff", "opening", "setup", "core", "revelation", "ending"]),
    ]
    pool = ranked[: max(8, min(len(ranked), 24))]
    for idx, (strategy, _) in enumerate(templates[:max_plans]):
        ordered = pool[idx:] + pool[:idx]
        sequence = ordered[: min(6, len(ordered))]
        if len(sequence) < 2:
            continue
        opening = [_item_id(sequence[0], "0")]
        core = [_item_id(x, str(i)) for i, x in enumerate(sequence[1:-1], 1)]
        ending = [_item_id(sequence[-1], str(len(sequence) - 1))]
        plan = build_story_plan(
            plan_id=f"plan-{strategy}-{idx + 1}",
            objective=objective,
            audience=audience,
            platform=platform,
            tone="editorial",
            style=strategy,
            opening=opening,
            setup=core[:1],
            escalation=core[1:2],
            core=core[2:] if len(core) > 2 else core,
            revelation=[],
            payoff=ending,
            ending=ending,
            total_duration=sum(float(x.get("duration", 0.0) or 0.0) for x in sequence),
            evidence={"candidate_ids": [_item_id(x, str(i)) for i, x in enumerate(sequence)], "generation_strategy": strategy},
            reasons=[f"generated using {strategy} editorial ordering"],
            risks=[],
            confidence=0.55,
        )
        plans.append(plan)
    return plans
