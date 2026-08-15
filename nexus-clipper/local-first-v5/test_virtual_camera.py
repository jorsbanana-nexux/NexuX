from virtual_camera import CameraPoint, SubjectObservation, build_camera_path, fallback_center_path, smooth_camera


def test_camera_path_stays_in_frame():
    obs = [
        SubjectObservation(0.0, 0.10, 0.20, 0.20, 0.30, 0.95),
        SubjectObservation(1.0, 0.30, 0.25, 0.20, 0.30, 0.95),
        SubjectObservation(2.0, 0.90, 0.30, 0.05, 0.10, 0.60),
    ]
    path = build_camera_path(obs)
    assert path
    for p in path:
        assert 0.0 <= p.cx <= 1.0
        assert 0.0 <= p.cy <= 1.0
        assert p.crop_w > 0
        assert p.crop_h > 0
        assert p.cx - p.crop_w / 2 >= -1e-9
        assert p.cx + p.crop_w / 2 <= 1.000000001
        assert p.cy - p.crop_h / 2 >= -1e-9
        assert p.cy + p.crop_h / 2 <= 1.000000001


def test_smoothing_reduces_motion():
    raw = [
        CameraPoint(0, 0.2, 0.5, 0.5, 0.89, 1),
        CameraPoint(1, 0.8, 0.5, 0.5, 0.89, 1),
    ]
    smoothed = smooth_camera(raw, alpha=0.2)
    assert abs(smoothed[1].cx - smoothed[0].cx) < abs(raw[1].cx - raw[0].cx)


def test_center_fallback():
    path = fallback_center_path([0, 1.5])
    assert all(p.cx == 0.5 and p.cy == 0.5 for p in path)
