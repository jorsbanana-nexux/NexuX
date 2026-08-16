from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis_world import SCHEMA_VERSION, build_analysis_world
from analysis_world_service import build_and_persist_world, load_world, world_path


def test_world_is_immutable_and_versioned() -> None:
    world = build_analysis_world(
        job_id="a" * 32,
        media={"duration": 120},
        transcript={"language": "id", "segments": []},
        audio_profiles={"clip-1": {"rhythm_score": 80.0}},
        candidates=[{"id": "clip-1", "start": 1.0, "end": 30.0}],
        confidence={"world": 1.0},
    )
    assert world.schema_version == SCHEMA_VERSION == "2.0"
    assert "media" in world.modalities
    assert "audio" in world.modalities
    assert "candidates" in world.modalities
    with pytest.raises(TypeError):
        world.transcript["language"] = "en"  # type: ignore[index]


def test_world_persists_and_round_trips(tmp_path: Path) -> None:
    world, path = build_and_persist_world(
        tmp_path,
        job_id="b" * 32,
        media={"duration": 45.0},
        transcript={"language": "en", "segments": [{"start": 0.0, "end": 1.0}]},
        scenes=[{"start": 0.0, "end": 5.0}],
        subjects=[{"candidate_id": "clip-1", "observations": []}],
        candidates=[{"id": "clip-1", "start": 0.0, "end": 20.0}],
        confidence={"world": 1.0},
    )
    assert path == world_path(tmp_path, "b" * 32)
    payload = load_world(tmp_path, "b" * 32)
    assert payload["schema_version"] == "2.0"
    assert payload["job_id"] == world.job_id
    assert payload["transcript"]["language"] == "en"
    json.loads(path.read_text(encoding="utf-8"))


def test_world_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        build_analysis_world(job_id="c" * 32, confidence={"world": 1.5})


def test_world_allows_missing_optional_modalities() -> None:
    world = build_analysis_world(job_id="d" * 32)
    assert world.modalities == frozenset()
    assert world.to_dict()["audio"]["profiles"] == {}
