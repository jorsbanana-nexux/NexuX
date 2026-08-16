from __future__ import annotations

from typing import Iterable
from story_plan import StoryPlan, build_story_plan


def judge_story_plans(plans: Iterable[StoryPlan], *, prefer_duration: float = 45.0) -> list[StoryPlan]:
    scored: list[tuple[float, StoryPlan]] = []
    for plan in plans:
        p = plan.validate()
        duration_fit = max(0.0, 1.0 - abs(p.total_duration - prefer_duration) / max(prefer_duration, 1.0))
        score = (
            0.20 * p.narrative_coherence + 0.18 * p.promise_payoff_integrity
            + 0.16 * p.context_integrity + 0.14 * p.retention_estimate
            + 0.10 * p.visual_feasibility + 0.08 * p.audio_feasibility
            + 0.08 * p.intent_match + 0.03 * p.diversity + 0.03 * duration_fit
        )
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    result: list[StoryPlan] = []
    for rank, (score, p) in enumerate(scored):
        decision = "KEEP" if rank == 0 and score >= 0.60 else ("REFINE" if score >= 0.45 else "REVIEW")
        result.append(build_story_plan(
            plan_id=p.plan_id, job_id=p.job_id, objective=p.objective, audience=p.audience,
            platform=p.platform, tone=p.tone, style=p.style, opening=p.opening,
            setup=p.setup, escalation=p.escalation, core=p.core, revelation=p.revelation,
            payoff=p.payoff, ending=p.ending, total_duration=p.total_duration,
            narrative_coherence=p.narrative_coherence, promise_payoff_integrity=p.promise_payoff_integrity,
            context_integrity=p.context_integrity, retention_estimate=p.retention_estimate,
            visual_feasibility=p.visual_feasibility, audio_feasibility=p.audio_feasibility,
            intent_match=p.intent_match, diversity=p.diversity, confidence=min(1.0, max(p.confidence, score)),
            evidence={**dict(p.evidence), "judge_score": round(score, 6), "judge_rank": rank + 1},
            reasons=tuple(p.reasons) + (f"plan judge score={score:.3f}",), risks=p.risks, decision=decision,
        ))
    return result


def select_best_story_plan(plans: Iterable[StoryPlan], *, prefer_duration: float = 45.0) -> StoryPlan | None:
    judged = judge_story_plans(plans, prefer_duration=prefer_duration)
    return judged[0] if judged else None
