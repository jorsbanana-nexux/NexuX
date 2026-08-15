from captions import phrases_from_words, PRESETS


def test_phrase_grouping_respects_word_limit():
    words = [
        {"word": "one", "start": 0.0, "end": 0.4},
        {"word": "two", "start": 0.4, "end": 0.8},
        {"word": "three", "start": 0.8, "end": 1.2},
        {"word": "four", "start": 1.2, "end": 1.6},
        {"word": "five", "start": 1.6, "end": 2.0},
    ]
    phrases = phrases_from_words(words, max_words=4)
    assert [len(p.words) for p in phrases] == [4, 1]


def test_phrase_grouping_breaks_on_pause():
    words = [
        {"word": "hello", "start": 0.0, "end": 0.3},
        {"word": "world", "start": 0.3, "end": 0.6},
        {"word": "again", "start": 1.2, "end": 1.5},
    ]
    phrases = phrases_from_words(words, max_gap=0.45)
    assert len(phrases) == 2


def test_required_presets_exist():
    assert {"karaoke", "pop_line", "deep_diver"}.issubset(PRESETS)
