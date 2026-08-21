from __future__ import annotations

from typing import Any
from story_plan import StoryPlan


def compile_story_plan(plan: StoryPlan, candidate_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    plan.validate()
    ordered: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    roles = [("opening", plan.opening), ("setup", *plan.setup), ("escalation", *plan.escalation), ("core", *plan.core), ("revelation", plan.revelation), ("payoff", plan.payoff), ("ending", plan.ending)]
    for role_entry in roles:
        role = role_entry[0]
        for node in role_entry[1:]:
            if not node:
                continue
            cid = str(node.get("candidate_id", ""))
            # Reusing the same candidate for two roles would overlap at render time —
            # keep the first occurrence (story books can lean on a candidate multiple
            # times conceptually, but the render plan cannot burn it twice).
            if cid in used_ids:
                continue
            source = candidate_index.get(cid)
            if source is None:
                raise ValueError(f"StoryPlan references unknown candidate: {cid}")
            ordered.append({"role": role, "candidate_id": cid, "start": float(source.get("start", 0.0)), "end": float(source.get("end", 0.0)), "duration": float(source.get("duration", 0.0)), "text": str(source.get("text", ""))})
            used_ids.add(cid)
    return {"schema_version": "1.0", "plan_id": plan.plan_id, "job_id": plan.job_id, "decision": plan.decision, "duration": sum(x["duration"] for x in ordered), "segments": ordered, "evidence": dict(plan.evidence)}


def validate_render_plan(compiled: dict[str, Any]) -> dict[str, Any]:
    segments = list(compiled.get("segments", []) or [])
    valid = bool(compiled.get("plan_id")) and bool(compiled.get("job_id")) and bool(segments)
    last_end = -1.0
    issues: list[str] = []
    for segment in segments:
        start, end = float(segment.get("start", 0.0)), float(segment.get("end", 0.0))
        if end <= start:
            issues.append(f"invalid segment timing: {segment.get('candidate_id')}")
        if start < last_end:
            issues.append(f"overlapping source segment: {segment.get('candidate_id')}")
        last_end = max(last_end, end)
    if not valid:
        issues.append("plan identity or segments missing")
    return {"valid": valid and not issues, "issues": issues, "segment_count": len(segments), "duration": round(sum(float(x.get("duration", 0.0)) for x in segments), 3)}
