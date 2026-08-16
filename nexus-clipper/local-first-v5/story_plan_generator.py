from __future__ import annotations

from typing import Any
from story_plan import StoryPlan, build_story_plan


def _item_id(item: dict[str, Any], fallback: str) -> str:
    return str(item.get("id") or fallback)


def generate_story_plans(candidates: list[dict[str, Any]], *, job_id: str, objective: str = "find_best_clips", audience: str = "general", platform: str = "short_form", target_duration: float = 45.0, max_plans: int = 5) -> list[StoryPlan]:
    if not candidates:
        return []
    ranked = sorted(candidates, key=lambda x: float(x.get("score", x.get("editorial_score", 0.0)) or 0.0), reverse=True)
    templates = ["hook_first", "context_first", "result_first", "tension_first", "payoff_first"]
    plans: list[StoryPlan] = []
    pool = ranked[: max(8, min(len(ranked), 24))]
    for idx, strategy in enumerate(templates[:max_plans]):
        ordered = pool[idx:] + pool[:idx]
        sequence = ordered[: min(6, len(ordered))]
        if len(sequence) < 2:
            continue
        ids = [_item_id(x, str(i)) for i, x in enumerate(sequence)]
        opening = {"candidate_id": ids[0], "role": "opening"}
        payoff = {"candidate_id": ids[-1], "role": "payoff"}
        ending = {"candidate_id": ids[-1], "role": "ending"}
        setup = [{"candidate_id": x, "role": "setup"} for x in ids[1:2]]
        escalation = [{"candidate_id": x, "role": "escalation"} for x in ids[2:3]]
        core = [{"candidate_id": x, "role": "core"} for x in ids[3:-1]]
        total_duration = sum(float(x.get("duration", 0.0) or 0.0) for x in sequence)
        plan = build_story_plan(
            plan_id=f"plan-{strategy}-{idx + 1}", job_id=job_id, objective=objective,
            audience=audience, platform=platform, tone="editorial", style=strategy,
            opening=opening, setup=setup, escalation=escalation, core=core,
            revelation={"candidate_id": ids[-2] if len(ids) > 2 else ids[-1], "role": "revelation"},
            payoff=payoff, ending=ending, total_duration=total_duration,
            narrative_coherence=0.55, promise_payoff_integrity=0.55, context_integrity=0.55,
            retention_estimate=0.55, visual_feasibility=0.65, audio_feasibility=0.65,
            intent_match=0.55, diversity=0.5, confidence=0.55,
            evidence={"candidate_ids": ids, "generation_strategy": strategy},
            reasons=[f"generated using {strategy} editorial ordering"], risks=[], decision="DRAFT",
        )
        plans.append(plan)
    return plans
