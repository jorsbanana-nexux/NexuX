from __future__ import annotations
from datetime import datetime, timedelta, timezone
from editorial_memory import EditorialMemoryEvent, EditorialPreferenceProfile, build_profile, personalized_adjustment
from editorial_memory_store import EditorialMemoryStore
from personalization_adapter import apply_personalization, feature_vector


def test_memory_builds_bounded_profile():
    now = datetime.now(timezone.utc)
    events = [EditorialMemoryEvent("1", "u", "hook", 1.0, created_at=now.isoformat()), EditorialMemoryEvent("2", "u", "context", -1.0, created_at=now.isoformat())]
    profile = build_profile(events, now=now)
    assert profile.user_id == "u"
    assert -1.0 <= profile.weights["hook"] <= 1.0
    assert -1.0 <= profile.weights["context"] <= 1.0
    assert 0.0 <= profile.confidence <= 1.0


def test_old_memory_decays():
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=365)
    profile = build_profile([EditorialMemoryEvent("1", "u", "hook", 1.0, created_at=old.isoformat())], now=now)
    assert abs(profile.weights["hook"]) < 0.1


def test_personal_adjustment_is_bounded():
    profile = EditorialPreferenceProfile("1.0", "u", {"hook": 1.0}, 20, 1.0, "")
    result = apply_personalization(0.5, profile, {"hook": 1.0})
    assert -0.15 <= result["adjustment"] <= 0.15
    assert result["applied"] is True


def test_empty_profile_is_noop():
    profile = EditorialPreferenceProfile("1.0", "", {}, 0, 0.0, "")
    assert personalized_adjustment(profile, {"hook": 1.0}) == 0.0


def test_store_round_trip(tmp_path):
    store = EditorialMemoryStore(tmp_path)
    store.append(EditorialMemoryEvent("1", "user-1", "hook", 1.0))
    events = store.events("user-1")
    assert len(events) == 1
    assert events[0].signal == "hook"
    assert store.profile("user-1").sample_count == 1


def test_feature_vector_is_stable():
    vector = feature_vector({"hook": 0.9, "context_quality": 0.8, "visual_energy": 0.7})
    assert vector["hook"] == 0.9
    assert vector["context"] == 0.8
    assert vector["visual_energy"] == 0.7
