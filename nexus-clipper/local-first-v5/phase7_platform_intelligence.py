from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class PlatformPolicy:
    platform: str
    aspect_ratio: str
    target_duration: float
    pacing: str
    caption_density: str
    hook_bias: float
    context_bias: float
    visual_intensity: float

PLATFORM_POLICIES = {
    "tiktok": PlatformPolicy("tiktok", "9:16", 35.0, "fast", "high", .92, .42, .90),
    "youtube_shorts": PlatformPolicy("youtube_shorts", "9:16", 45.0, "medium_fast", "high", .86, .58, .82),
    "instagram_reels": PlatformPolicy("instagram_reels", "9:16", 40.0, "medium_fast", "high", .84, .55, .88),
    "linkedin": PlatformPolicy("linkedin", "4:5", 55.0, "measured", "medium", .62, .88, .55),
    "x": PlatformPolicy("x", "9:16", 45.0, "fast", "medium", .78, .60, .72),
    "generic": PlatformPolicy("generic", "9:16", 45.0, "medium", "medium", .75, .65, .70),
}

@dataclass(frozen=True)
class EditorialProfile:
    profile_id: str
    preferences: Mapping[str, Any]

    def merge(self, overrides: Mapping[str, Any] | None = None) -> "EditorialProfile":
        values = dict(self.preferences)
        values.update(dict(overrides or {}))
        return EditorialProfile(self.profile_id, values)

def resolve_platform_policy(platform: str, overrides: Mapping[str, Any] | None = None) -> PlatformPolicy:
    base = PLATFORM_POLICIES.get(str(platform).lower(), PLATFORM_POLICIES["generic"])
    values = dict(overrides or {})
    return PlatformPolicy(base.platform, str(values.get("aspect_ratio", base.aspect_ratio)), float(values.get("target_duration", base.target_duration)), str(values.get("pacing", base.pacing)), str(values.get("caption_density", base.caption_density)), float(values.get("hook_bias", base.hook_bias)), float(values.get("context_bias", base.context_bias)), float(values.get("visual_intensity", base.visual_intensity)))

def resolve_creative_policy(*, platform: str, mode: str = "balanced", profile: EditorialProfile | None = None) -> dict[str, Any]:
    profile = profile or EditorialProfile("default", {})
    mode_values = {
        "viral": {"hook_bias": .98, "context_bias": .35, "visual_intensity": .95, "pacing": "fast", "caption_density": "high"},
        "educational": {"hook_bias": .68, "context_bias": .95, "visual_intensity": .55, "pacing": "measured", "caption_density": "medium"},
        "storytelling": {"hook_bias": .82, "context_bias": .90, "visual_intensity": .72, "pacing": "dynamic", "caption_density": "medium"},
        "authority": {"hook_bias": .62, "context_bias": .94, "visual_intensity": .52, "pacing": "measured", "caption_density": "medium"},
        "balanced": {},
    }
    p = resolve_platform_policy(platform)
    return {"platform": p.platform, "aspect_ratio": p.aspect_ratio, "target_duration": p.target_duration, "hook_bias": p.hook_bias, "context_bias": p.context_bias, "visual_intensity": p.visual_intensity, "pacing": p.pacing, "caption_density": p.caption_density, **mode_values.get(mode, {}), **dict(profile.preferences)}
