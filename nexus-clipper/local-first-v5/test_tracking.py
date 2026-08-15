from tracking import Detection, assign_tracks, primary_track


def test_assign_tracks_keeps_nearby_identity():
    points = assign_tracks([
        Detection(0.0, 0.10, 0.10, 0.20, 0.20, 0.9),
        Detection(0.5, 0.12, 0.11, 0.20, 0.20, 0.9),
        Detection(1.0, 0.14, 0.12, 0.20, 0.20, 0.9),
    ])
    assert len({p.track_id for p in points}) == 1


def test_primary_track_prefers_persistent_large_subject():
    points = assign_tracks([
        Detection(0.0, 0.05, 0.05, 0.10, 0.10, 0.8),
        Detection(0.0, 0.40, 0.20, 0.30, 0.35, 0.9),
        Detection(1.0, 0.07, 0.05, 0.10, 0.10, 0.8),
        Detection(1.0, 0.42, 0.21, 0.30, 0.35, 0.9),
    ])
    assert primary_track(points) is not None
