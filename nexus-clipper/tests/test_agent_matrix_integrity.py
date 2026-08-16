from __future__ import annotations

import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from agents import AGENT_REGISTRY, get_agent_matrix, summary


def test_registry_contains_exactly_25_agents():
    assert set(AGENT_REGISTRY) == {f"agent_{index:02d}" for index in range(1, 26)}


def test_matrix_contains_exactly_25_agents():
    matrix = get_agent_matrix()
    assert set(matrix) == set(AGENT_REGISTRY)
    assert sum(summary().values()) == 25


def test_every_agent_module_imports():
    for index in range(1, 26):
        importlib.import_module(f"agents.agent_{index:02d}_{_module_suffix(index)}")


def test_planning_and_disabled_agents_are_not_canonical_stages():
    matrix = get_agent_matrix()
    for info in matrix.values():
        if info["status"] in {"planning", "disabled"}:
            assert info["canonical_stage"] not in {"render", "qa-output"}


def _module_suffix(index: int) -> str:
    names = {
        1: "master_brain", 2: "url_fetcher", 3: "keyword_optimizer", 4: "content_planner",
        5: "competitor_analyzer", 6: "narration_writer", 7: "voice_cloner", 8: "emotion_controller",
        9: "spatial_8d_audio", 10: "breath_injector", 11: "scene_segmenter", 12: "subject_tracker",
        13: "quality_checker", 14: "lip_sync", 15: "broll_blocker", 16: "subtitle_designer",
        17: "sound_designer", 18: "music_selector", 19: "transition_ai", 20: "professional_editor",
        21: "quality_inspector", 22: "audience_predictor", 23: "auto_improver", 24: "omni_exporter",
        25: "seo_generator",
    }
    return names[index]
