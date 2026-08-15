from pathlib import Path

import pytest

from fonts import MAX_FONT_BYTES, validate_font
from youtube import validate_youtube_url


def test_youtube_host_is_case_insensitive_and_rejects_userinfo():
    assert validate_youtube_url("HTTPS://WWW.YOUTUBE.COM/watch?v=abc")
    with pytest.raises(ValueError):
        validate_youtube_url("https://user:pass@youtube.com/watch?v=abc")
    with pytest.raises(ValueError):
        validate_youtube_url("https://example.com/watch?v=abc")


def test_font_size_guard_and_signature(tmp_path: Path):
    small = tmp_path / "tiny.ttf"
    small.write_bytes(b"0" * 255)
    with pytest.raises(ValueError):
        validate_font(small)

    huge = tmp_path / "huge.ttf"
    with huge.open("wb") as handle:
        handle.write(b"\x00\x01\x00\x00")
        handle.truncate(MAX_FONT_BYTES + 1)
    with pytest.raises(ValueError):
        validate_font(huge)
