from targeted_retrieval import RetrievalRange, parse_vtt


def test_parse_vtt_builds_nexux_transcript_shape():
    transcript = parse_vtt(
        """WEBVTT\n\n00:00.000 --> 00:02.500\nHello <c>world</c>\n\n00:02.500 --> 00:05.000\nThis is NexuX.\n"""
    )
    assert len(transcript["segments"]) == 2
    assert transcript["segments"][0]["start"] == 0.0
    assert transcript["segments"][0]["end"] == 2.5
    assert transcript["segments"][0]["text"] == "Hello world"
    assert transcript["segments"][1]["text"] == "This is NexuX."
    assert transcript["source"] == "youtube_vtt"


def test_retrieval_range_never_goes_before_zero():
    padded = RetrievalRange(2.0, 12.0).padded(before=8.0, after=5.0)
    assert padded.start == 0.0
    assert padded.end == 17.0


def test_retrieval_range_keeps_requested_window_inside_padded_window():
    requested = RetrievalRange(120.0, 155.0)
    padded = requested.padded(before=6.0, after=8.0)
    assert padded.start == 114.0
    assert padded.end == 163.0
    assert padded.start <= requested.start <= requested.end <= padded.end
