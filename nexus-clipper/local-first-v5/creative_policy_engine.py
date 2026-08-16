from __future__ import annotations

from typing import Any, Mapping
from phase7_platform_intelligence import EditorialProfile, resolve_creative_policy


def apply_policy_to_candidates(candidates: list[dict[str, Any]], policy: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    hook_bias = float(policy.get("hook_bias", .75))
    context_bias = float(policy.get("context_bias", .65))
    for item in candidates:
        candidate = dict(item)
        hook = float(candidate.get("hook_score", candidate.get("hook", 0.0)) or 0.0)
        context = float(candidate.get("context_score", candidate.get("context", 0.0)) or 0.0)
        candidate["platform_policy"] = dict(policy)
        candidate["creative_fit"] = round(max(0.0, min(1.0, hook * hook_bias + context * context_bias)), 4)
        result.append(candidate)
    return sorted(result, key=lambda x: float(x.get("creative_fit", 0.0)), reverse=True)


def resolve_request_policy(*, platform: str, mode: str = "balanced", profile_id: str = "default", profile_preferences: Mapping[str, Any] | None = None) -> dict[str, Any]:
    profile = EditorialProfile(profile_id, dict(profile_preferences or {}))
    return resolve_creative_policy(platform=platform, mode=mode, profile=profile)
