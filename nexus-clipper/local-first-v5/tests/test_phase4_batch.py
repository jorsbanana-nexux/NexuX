from __future__ import annotations

from story_plan import build_story_plan
from story_plan_generator import generate_story_plans
from story_plan_judge import judge_story_plans, select_best_story_plan
from story_plan_compiler import compile_story_plan, validate_render_plan


def candidates():
    return [
        {"id":"a","score":0.95,"duration":10,"start":0,"end":10,"text":"Why did it fail?"},
        {"id":"b","score":0.85,"duration":12,"start":12,"end":24,"text":"The real problem was cost."},
        {"id":"c","score":0.80,"duration":11,"start":25,"end":36,"text":"We changed the model."},
        {"id":"d","score":0.90,"duration":8,"start":37,"end":45,"text":"Finally, margin recovered."},
    ]


def test_generate_and_judge_plans():
    plans = generate_story_plans(candidates(), job_id="job-1", max_plans=3)
    assert len(plans) == 3
    judged = judge_story_plans(plans)
    assert judged
    assert judged[0].decision in {"KEEP", "REFINE", "REVIEW"}
    assert select_best_story_plan(plans) is not None


def test_compile_and_validate_story_plan():
    plan = build_story_plan(
        plan_id="p1", job_id="job-1", objective="find_best_clips",
        opening={"candidate_id":"a"}, setup=[{"candidate_id":"b"}],
        core=[{"candidate_id":"c"}], payoff={"candidate_id":"d"},
        ending={"candidate_id":"d"}, total_duration=41,
        narrative_coherence=.8, promise_payoff_integrity=.8,
        context_integrity=.8, retention_estimate=.8, visual_feasibility=.8,
        audio_feasibility=.8, intent_match=.8, diversity=.8, confidence=.8,
    )
    compiled = compile_story_plan(plan, {x["id"]: x for x in candidates()})
    checked = validate_render_plan(compiled)
    assert checked["valid"] is True
    assert checked["segment_count"] >= 3
