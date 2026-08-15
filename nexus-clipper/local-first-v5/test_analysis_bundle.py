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
