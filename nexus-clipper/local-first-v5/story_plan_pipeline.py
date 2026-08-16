from __future__ import annotations

from typing import Any
from analysis_world import AnalysisWorld
from story_plan_generator import generate_story_plans
from story_plan_judge import judge_story_plans


def plan_from_world(world: AnalysisWorld, *, limit: int = 5) -> list[dict[str, Any]]:
    world.validate()
    intent = dict(world.editorial.get("intent", {}) or {})
    plans = generate_story_plans(
        [dict(x) for x in world.candidates],
        job_id=world.job_id,
        objective=str(intent.get("objective", "find_best_clips")),
        audience=str(intent.get("audience", "general")),
        platform=str(intent.get("platform", "short_form")),
        target_duration=float(intent.get("target_duration", 45.0) or 45.0),
        max_plans=limit,
    )
    judged = judge_story_plans(plans, prefer_duration=float(intent.get("target_duration", 45.0) or 45.0))
    return [p.to_dict() for p in judged]
