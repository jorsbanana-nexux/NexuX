from phase7_platform_intelligence import EditorialProfile, resolve_platform_policy, resolve_creative_policy
from creative_policy_engine import apply_policy_to_candidates


def test_platform_policy_defaults_and_overrides():
    policy = resolve_platform_policy("youtube_shorts")
    assert policy.aspect_ratio == "9:16"
    assert policy.target_duration > 0
    overridden = resolve_platform_policy("youtube_shorts", {"target_duration": 30})
    assert overridden.target_duration == 30


def test_profile_and_creative_mode_merge():
    profile = EditorialProfile("creator-1", {"caption_density": "low", "pacing": "calm"})
    policy = resolve_creative_policy(platform="linkedin", mode="educational", profile=profile)
    assert policy["caption_density"] == "low"
    assert policy["pacing"] == "calm"
    assert policy["context_bias"] >= .9


def test_candidate_policy_fit_is_deterministic():
    policy = resolve_creative_policy(platform="tiktok", mode="viral")
    candidates = [{"id": "a", "hook_score": .9, "context_score": .4}, {"id": "b", "hook_score": .5, "context_score": .9}]
    result = apply_policy_to_candidates(candidates, policy)
    assert result[0]["platform_policy"]["platform"] == "tiktok"
    assert all(0.0 <= x["creative_fit"] <= 1.0 for x in result)
