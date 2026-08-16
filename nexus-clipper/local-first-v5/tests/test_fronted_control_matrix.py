from __future__ import annotations

import json
from pathlib import Path

from server import GenerateRequest


ROOT = Path(__file__).resolve().parents[1]


def test_fronted_control_matrix_covers_generate_request_fields() -> None:
    matrix = json.loads((ROOT / "control_engine_matrix.json").read_text(encoding="utf-8"))
    controls = set(matrix["controls"])
    model_fields = set(GenerateRequest.model_fields)
    assert model_fields <= controls
    assert all(item.get("rendered") is True for item in matrix["controls"].values())


def test_fronted_payload_can_reach_all_render_controls() -> None:
    request = GenerateRequest(
        youtube_url="https://youtube.com/watch?v=benchmark",
        target_duration=52,
        aspect_ratio="16:9",
        subtitle_style="minimalist",
        font="Poppins",
        font_size=64,
        primary_color="#123456",
        highlight_color="#ABCDEF",
        stroke_color="#000000",
        stroke_width=7,
        position="top",
        animation="typewriter",
        auto_zoom=False,
        face_tracking=True,
        clip_count=10,
        language="en",
        normalize_audio=False,
        emoji_enabled=True,
    )
    assert request.target_duration == 52
    assert request.aspect_ratio == "16:9"
    assert request.font == "Poppins"
    assert request.font_size == 64
    assert request.position == "top"
    assert request.animation == "typewriter"
    assert request.face_tracking is True
    assert request.auto_zoom is False
    assert request.clip_count == 10
    assert request.normalize_audio is False
    assert request.emoji_enabled is True
