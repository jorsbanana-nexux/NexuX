from dataclasses import dataclass

from caption_runtime import _fragments_for_word


@dataclass(frozen=True)
class Keep:
    source_start: float
    source_end: float


@dataclass(frozen=True)
class Timeline:
    keep_ranges: tuple[Keep, ...]


def test_word_crossing_removed_range_is_split_not_dropped():
    timeline = Timeline((Keep(0.0, 1.0), Keep(2.0, 3.0)))
    fragments = _fragments_for_word({"word": "hello", "start": 0.8, "end": 2.2}, timeline)
    assert [(round(item["start"], 3), round(item["end"], 3)) for item in fragments] == [(0.8, 1.0), (2.0, 2.2)]


def test_word_fully_inside_removed_range_has_no_fragment():
    timeline = Timeline((Keep(0.0, 1.0), Keep(2.0, 3.0)))
    assert _fragments_for_word({"word": "hello", "start": 1.2, "end": 1.8}, timeline) == []
