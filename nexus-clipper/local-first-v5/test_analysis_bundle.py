import pytest

from analysis_bundle import SCHEMA_VERSION, build_analysis_bundle


def test_analysis_bundle_is_versioned_and_collects_audio_profiles():
    candidates = [
        {"id": "c1", "start": 0, "end": 30, "audio_profile": {"rhythm_score": 82.0}},
        {"id": "c2", "start": 40, "end": 70},
    ]
    bundle = build_analysis_bundle(
        {"segments": [{"start": 0, "end": 1, "text": "hello"}]},
        candidates,
        [{"start": 0, "end": 10}],
        [{"timestamp": 0, "faces": []}],
    )
    assert bundle.schema_version == SCHEMA_VERSION
    assert bundle.audio_profiles == {"c1": {"rhythm_score": 82.0}}
    payload = bundle.to_dict()
    assert payload["candidates"][0]["id"] == "c1"
    assert payload["scenes"][0]["start"] == 0


def test_analysis_bundle_does_not_mutate_input_lists():
    candidates = [{"id": "c1"}]
    scenes = [{"start": 0, "end": 2}]
    subjects = [{"timestamp": 1, "faces": []}]
    bundle = build_analysis_bundle({"segments": []}, candidates, scenes, subjects)
    candidates[0]["id"] = "changed"
    scenes[0]["start"] = 99
    subjects[0]["timestamp"] = 99
    assert bundle.candidates[0]["id"] == "c1"
    assert bundle.scenes[0]["start"] == 0
    assert bundle.subjects[0]["timestamp"] == 1


def test_analysis_bundle_is_deeply_immutable():
    bundle = build_analysis_bundle(
        {"segments": [{"text": "hello"}]},
        [{"id": "c1", "audio_profile": {"rhythm_score": 82.0}}],
        [{"start": 0, "end": 10}],
        [{"timestamp": 0, "faces": []}],
    )
    with pytest.raises(TypeError):
        bundle.transcript["segments"] = []
    with pytest.raises(TypeError):
        bundle.audio_profiles["c1"]["rhythm_score"] = 10.0


def test_timeline_reuses_candidate_audio_profile(tmp_path, monkeypatch):
    import timeline as module

    monkeypatch.setattr(module, "analyze_audio", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected audio re-analysis")))
    monkeypatch.setattr(module, "detect_silence", lambda *args, **kwargs: [])

    video = tmp_path / "placeholder.mp4"
    timeline = module.build_timeline(
        video,
        {"segments": []},
        {"start": 0.0, "end": 20.0, "audio_profile": {"rhythm_score": 80.0}},
    )
    assert timeline.audio_profile["rhythm_score"] == 80.0


def test_timeline_keeps_context_sensitive_words():
    import timeline as module

    segments = [{
        "words": [
            {"word": "jadi", "start": 1.0, "end": 1.2},
            {"word": "um", "start": 2.0, "end": 2.2},
        ]
    }]
    cuts = module.detect_fillers(segments, 0.0, 4.0)
    assert len(cuts) == 1
    assert cuts[0].reason == "filler"
    assert cuts[0].start < 2.0 < cuts[0].end
