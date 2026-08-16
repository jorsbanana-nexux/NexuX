"""Runtime truth for the 25-agent matrix.

The matrix preserves every agent while preventing planning-only or disabled
components from masquerading as canonical media pipeline stages.
"""

from __future__ import annotations

from typing import Final

STATUSES: Final[tuple[str, ...]] = ("active", "adapter", "planning", "optional", "disabled")

AGENT_MATRIX: Final[dict[str, dict[str, str]]] = {
    "agent_01": {"status": "adapter", "role": "project_orchestrator", "canonical_stage": "job-control"},
    "agent_02": {"status": "adapter", "role": "url_fetcher", "canonical_stage": "ingest"},
    "agent_03": {"status": "planning", "role": "keyword_expansion", "canonical_stage": "editorial-metadata"},
    "agent_04": {"status": "planning", "role": "content_planner", "canonical_stage": "generation-mode"},
    "agent_05": {"status": "planning", "role": "competitor_analysis", "canonical_stage": "research"},
    "agent_06": {"status": "planning", "role": "narration_writer", "canonical_stage": "generation-mode"},
    "agent_07": {"status": "optional", "role": "voice_synthesis", "canonical_stage": "generation-mode"},
    "agent_08": {"status": "planning", "role": "emotion_mapping", "canonical_stage": "editorial-enrichment"},
    "agent_09": {"status": "disabled", "role": "spatial_audio", "canonical_stage": "audio"},
    "agent_10": {"status": "planning", "role": "breath_injection_plan", "canonical_stage": "generation-mode"},
    "agent_11": {"status": "adapter", "role": "scene_segmentation", "canonical_stage": "vision"},
    "agent_12": {"status": "adapter", "role": "subject_tracking", "canonical_stage": "vision"},
    "agent_13": {"status": "adapter", "role": "visual_quality", "canonical_stage": "qa"},
    "agent_14": {"status": "disabled", "role": "lip_sync", "canonical_stage": "translation"},
    "agent_15": {"status": "active", "role": "broll_policy_guard", "canonical_stage": "policy"},
    "agent_16": {"status": "adapter", "role": "subtitle_design_metadata", "canonical_stage": "captions"},
    "agent_17": {"status": "planning", "role": "sound_design_plan", "canonical_stage": "audio"},
    "agent_18": {"status": "planning", "role": "music_selection_plan", "canonical_stage": "audio"},
    "agent_19": {"status": "planning", "role": "transition_plan", "canonical_stage": "timeline"},
    "agent_20": {"status": "adapter", "role": "legacy_editor_guard", "canonical_stage": "render"},
    "agent_21": {"status": "adapter", "role": "render_qa", "canonical_stage": "qa"},
    "agent_22": {"status": "planning", "role": "audience_prediction", "canonical_stage": "editorial"},
    "agent_23": {"status": "planning", "role": "retry_policy", "canonical_stage": "qa-feedback"},
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
    expected = {f"agent_{index:02d}" for index in range(1, 26)}
    actual = set(AGENT_MATRIX)
    if actual != expected:
        raise RuntimeError(f"Agent matrix mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    invalid = {key: value["status"] for key, value in AGENT_MATRIX.items() if value["status"] not in STATUSES}
    if invalid:
        raise RuntimeError(f"Invalid agent statuses: {invalid}")

validate_matrix()
