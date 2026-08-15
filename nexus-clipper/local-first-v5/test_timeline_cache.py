import timeline as timeline_module
from timeline import build_timeline


def test_timeline_reuses_ranked_audio_profile(monkeypatch):
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("audio analysis must be reused from candidate cache")

    monkeypatch.setattr(timeline_module, "analyze_audio", fail_if_called)
    monkeypatch.setattr(timeline_module, "detect_silence", lambda *args, **kwargs: [])
    monkeypatch.setattr(timeline_module, "detect_fillers", lambda *args, **kwargs: [])
    monkeypatch.setattr(timeline_module, "detect_repetition", lambda *args, **kwargs: [])

    timeline = build_timeline(
        video=__import__("pathlib").Path("unused.mp4"),
        transcript={"segments": []},
        clip={
            "start": 0.0,
            "end": 30.0,
            "audio_profile": {"rhythm_score": 82.0, "speech_density": 4.5},
        },
    )
    assert timeline.audio_profile["rhythm_score"] == 82.0
    assert timeline.duration_after == 30.0
