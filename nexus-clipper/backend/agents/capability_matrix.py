"""Runtime truth for the 20-agent matrix (V8.0).

V8.0: Removed placeholder agents (11, 12, 13, 20, 21).
Their canonical functionality lives in engine modules:
- scene segmentation → engine/vision.py
- subject tracking → engine/vision.py
- visual quality → engine/critic.py
- editorial decision loop → engine/pipeline.py
- render QA → engine/critic.py

Remaining agents that matter are activated,
agents that were stubs are either upgraded or honestly disabled.
"""

from __future__ import annotations

from typing import Final

STATUSES: Final[tuple[str, ...]] = ("active", "adapter", "planning", "optional", "disabled")

AGENT_MATRIX: Final[dict[str, dict[str, str]]] = {
    "agent_01": {"status": "active", "role": "pipeline_orchestrator", "canonical_stage": "orchestration"},
    "agent_02": {"status": "adapter", "role": "url_fetcher", "canonical_stage": "ingest"},
    "agent_03": {"status": "planning", "role": "keyword_expansion", "canonical_stage": "editorial-metadata"},
    "agent_04": {"status": "planning", "role": "content_planner", "canonical_stage": "generation-mode"},
    "agent_05": {"status": "planning", "role": "competitor_analysis", "canonical_stage": "research"},
    "agent_06": {"status": "planning", "role": "narration_writer", "canonical_stage": "generation-mode"},
    "agent_07": {"status": "optional", "role": "voice_synthesis", "canonical_stage": "generation-mode"},
    "agent_08": {"status": "active", "role": "emotion_arc_analysis", "canonical_stage": "editorial-enrichment"},
    "agent_09": {"status": "disabled", "role": "spatial_audio_honest_stub", "canonical_stage": "audio"},
    "agent_10": {"status": "planning", "role": "breath_injection_plan", "canonical_stage": "generation-mode"},
    "agent_14": {"status": "disabled", "role": "lip_sync", "canonical_stage": "translation"},
    "agent_15": {"status": "active", "role": "broll_policy_guard", "canonical_stage": "policy"},
    "agent_16": {"status": "adapter", "role": "subtitle_design_metadata", "canonical_stage": "captions"},
    "agent_17": {"status": "planning", "role": "sound_design_plan", "canonical_stage": "audio"},
    "agent_18": {"status": "planning", "role": "music_selection_plan", "canonical_stage": "audio"},
    "agent_19": {"status": "planning", "role": "transition_plan", "canonical_stage": "timeline"},
    "agent_22": {"status": "active", "role": "audience_prediction", "canonical_stage": "editorial"},
    "agent_23": {"status": "active", "role": "diagnostic_improvement", "canonical_stage": "qa-feedback"},
    "agent_24": {"status": "adapter", "role": "export_planning", "canonical_stage": "export"},
    "agent_25": {"status": "planning", "role": "seo_metadata", "canonical_stage": "distribution"},
}


def get_agent_matrix() -> dict[str, dict[str, str]]:
    return {key: dict(value) for key, value in AGENT_MATRIX.items()}


def summary() -> dict[str, int]:
    result = {status: 0 for status in STATUSES}
    for info in AGENT_MATRIX.values():
        result[info["status"]] += 1
    return result


def validate_matrix() -> None:
    expected = {f"agent_{index:02d}" for index in [1,2,3,4,5,6,7,8,9,10,14,15,16,17,18,19,22,23,24,25]}
    actual = set(AGENT_MATRIX)
    if actual != expected:
        raise RuntimeError(f"Agent matrix mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    invalid = {key: value["status"] for key, value in AGENT_MATRIX.items() if value["status"] not in STATUSES}
    if invalid:
        raise RuntimeError(f"Invalid agent statuses: {invalid}")

validate_matrix()
