from __future__ import annotations
from typing import Any, Mapping
from editorial_memory import EditorialPreferenceProfile, personalized_adjustment

SAFE_SIGNAL_MAP = {
    "prefers_fast_pacing": "pacing",
    "prefers_context": "context",
    "prefers_strong_hooks": "hook",
    "prefers_emotional": "emotional",
    "prefers_clean_captions": "caption",
    "prefers_tight_cuts": "cut_density",
    "prefers_visual_motion": "visual_energy",
}

def apply_personalization(base_score: float, profile: EditorialPreferenceProfile, features: Mapping[str, float]) -> dict[str, Any]:
    adjustment = personalized_adjustment(profile, features)
    final_score = max(0.0, min(1.0, float(base_score) + adjustment))
    return {
        "base_score": max(0.0, min(1.0, float(base_score))),
        "adjustment": round(adjustment, 6),
        "final_score": round(final_score, 6),
        "profile_confidence": profile.confidence,
        "applied": bool(profile.user_id and profile.confidence > 0),
        "guardrail": "bounded_personal_adjustment",
    }

def feature_vector(candidate: Mapping[str, Any]) -> dict[str, float]:
    return {
        "hook": float(candidate.get("hook", 0.0) or 0.0),
        "context": float(candidate.get("context", candidate.get("context_quality", 0.0)) or 0.0),
        "pacing": float(candidate.get("pacing", 0.0) or 0.0),
        "emotional": float(candidate.get("emotional", 0.0) or 0.0),
        "caption": float(candidate.get("caption_quality", 0.0) or 0.0),
        "cut_density": float(candidate.get("cut_density", 0.0) or 0.0),
        "visual_energy": float(candidate.get("visual_energy", 0.0) or 0.0),
    }
