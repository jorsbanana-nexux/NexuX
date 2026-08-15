from timeline import Cut, EditTimeline, KeepRange, _merge_cuts, remap_word


def test_merge_cuts_is_stable():
    cuts = _merge_cuts(
        [Cut(1.0, 2.0, "silence"), Cut(1.98, 2.5, "filler"), Cut(5.0, 5.4, "silence")],
        0.0,
        10.0,
    )
    assert [(c.start, c.end) for c in cuts] == [(1.0, 2.5), (5.0, 5.4)]


def test_source_to_output_and_word_remap():
    timeline = EditTimeline(
        source_start=0.0,
        source_end=10.0,
        duration_before=10.0,
        duration_after=8.0,
        cuts=(Cut(4.0, 6.0, "silence"),),
        keep_ranges=(
            KeepRange(0.0, 4.0, 0.0, 4.0),
            KeepRange(6.0, 10.0, 4.0, 8.0),
        ),
    )
    assert timeline.source_to_output(2.0) == 2.0
    assert timeline.source_to_output(8.0) == 6.0
    assert timeline.source_to_output(5.0) is None
    mapped = remap_word({"word": "hello", "start": 7.0, "end": 7.5}, timeline)
    assert mapped == {"word": "hello", "start": 5.0, "end": 5.5}
