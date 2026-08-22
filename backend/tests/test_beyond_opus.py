r"""
NexuX V9.6 — "Beyond Opus" Feature Tests
=========================================
Covers the three new engines that go beyond Opus Clip:
- Smart Cut (engine/smart_cut.py) — real jump-cuts, not just detection
- Retention Heatmap (engine/retention_heatmap.py) — per-second analytics
- Hook Lab (engine/hook_lab.py) — hook variants + transparent CTR scoring
Plus the new extras endpoints for retention & hook-lab.
"""
import json
import pytest

from engine.smart_cut import (
    compute_keep_segments, compress_time, remap_transcript, SmartCutResult,
)
from engine.retention_heatmap import predict_retention_curve
from engine.hook_lab import predict_title_ctr, generate_hook_variants


# ── Fixtures ──

def _word(text, start, end):
    return {"word": text, "start": start, "end": end}


def _dense_words(start, count, step=0.4, word="word"):
    return [_word(word, start + i * step, start + i * step + 0.35)
            for i in range(count)]


@pytest.fixture()
def word_transcript():
    """Realistic 30s word-level transcript: dense speech, one 2.5s silence
    (2.0→4.5), one 'um' filler (4.5→4.9), then dense speech to 30s."""
    words = (_dense_words(0.0, 5) + [_word("um", 4.5, 4.9)]
             + _dense_words(5.0, 63))
    return {
        "segments": [{
            "start": 0.0, "end": 30.0,
            "text": " ".join(w["word"] for w in words),
            "words": words,
        }],
        "text": " ".join(w["word"] for w in words),
    }


@pytest.fixture()
def segment_transcript():
    """Realistic 30s segment-level transcript with a 3s gap (2→5s)."""
    return {
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "First sentence here."},
            {"start": 5.0, "end": 30.0,
             "text": "Second sentence continues with many more words "
                     "spoken steadily until the clip window ends."},
        ],
        "text": "First sentence here. Second sentence continues.",
    }


# ── Smart Cut ──

class TestSmartCut:
    def test_silence_cut_word_level(self, word_transcript):
        res = compute_keep_segments(word_transcript, 0.0, 30.0, max_silence=0.5)
        # 2s gap (0.4→2.5) minus padding is cut; 'um' filler also cut
        assert res.silence_count == 1
        assert any(r["reason"] == "silence" for r in res.removed_segments)

    def test_filler_cut_word_level(self, word_transcript):
        res = compute_keep_segments(
            word_transcript, 0.0, 30.0, max_silence=0.5, remove_fillers=True)
        assert res.filler_count >= 1
        assert any(r["reason"] == "filler" for r in res.removed_segments)

    def test_no_filler_cut_when_disabled(self, word_transcript):
        res = compute_keep_segments(
            word_transcript, 0.0, 30.0, max_silence=0.5, remove_fillers=False)
        assert res.filler_count == 0

    def test_segment_level_silence(self, segment_transcript):
        res = compute_keep_segments(segment_transcript, 0.0, 30.0, max_silence=0.5)
        assert res.silence_count == 1
        assert len(res.keep_segments) == 2
        assert res.removed_seconds > 1.0

    def test_empty_transcript_keeps_everything(self):
        res = compute_keep_segments({"segments": []}, 0.0, 10.0)
        assert res.keep_segments == [(0.0, 10.0)]

    def test_safety_refusal_on_huge_removal(self):
        # Transcript where nearly everything is filler → refuse to cut
        words = [_word("um", t, t + 0.3) for t in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]]
        t = {"segments": [{"start": 0.0, "end": 3.0, "text": "um um um",
                            "words": words}]}
        res = compute_keep_segments(t, 0.0, 3.0, max_silence=0.2)
        assert res.keep_segments == [(0.0, 3.0)]
        assert res.removed_pct == 0.0

    def test_compress_time_mapping(self):
        keep = [(0.0, 1.0), (2.0, 3.0)]
        assert compress_time(0.5, keep) == 0.5
        assert compress_time(2.5, keep) == 1.5
        assert compress_time(1.5, keep) is None  # inside removed range

    def test_remap_transcript_drops_cut_words(self, word_transcript):
        res = compute_keep_segments(word_transcript, 0.0, 30.0, max_silence=0.5)
        remapped = remap_transcript(word_transcript, res.keep_segments)
        all_words = [w["word"].lower()
                     for s in remapped["segments"] for w in s["words"]]
        assert "um" not in all_words
        assert "word" in all_words
        # Retimes start at 0
        assert remapped["segments"][0]["start"] == 0.0
        # Timeline compressed by the removed seconds
        last_end = remapped["segments"][-1]["end"]
        assert last_end <= res.new_duration + 0.01

    def test_to_dict_shape(self, word_transcript):
        res = compute_keep_segments(word_transcript, 0.0, 30.0)
        d = res.to_dict()
        assert {"keep_segments", "removed_segments", "original_duration",
                "new_duration", "removed_seconds", "removed_pct",
                "filler_count", "silence_count"} <= set(d)

    def test_worth_cutting_thresholds(self):
        r = SmartCutResult(keep_segments=[(0, 30)], new_duration=30.0,
                           original_duration=30.0, removed_seconds=0.0)
        assert not r.worth_cutting
        r2 = SmartCutResult(keep_segments=[(0, 10), (11, 30)],
                            new_duration=29.0, original_duration=31.0,
                            removed_seconds=2.0)
        assert r2.worth_cutting


# ── Retention Heatmap ──

class TestRetentionHeatmap:
    def test_curve_shape_and_grade(self, segment_transcript):
        clip = {"start": 0.0, "end": 30.0}
        out = predict_retention_curve(clip, segment_transcript, hook_strength=0.7)
        assert out["curve"]
        assert 0 < out["avg_retention"] <= 100
        assert out["grade"] in ("S", "A", "B", "C", "D")
        assert out["hook_strength"] == 0.7
        first = out["curve"][0]
        assert {"t", "retention", "speech_rate", "silent", "spike"} <= set(first)

    def test_empty_clip_returns_empty(self):
        out = predict_retention_curve({"start": 5, "end": 5}, {"segments": []})
        assert out["curve"] == []
        assert out["avg_retention"] == 0.0

    def test_silence_penalized(self):
        # Segment transcript has a 3s silent gap (2→5s)
        clip = {"start": 0.0, "end": 30.0}
        transcript = {"segments": [
            {"start": 0.0, "end": 2.0, "text": "Words words words"},
            {"start": 5.0, "end": 8.0, "text": "More words here"},
        ]}
        out = predict_retention_curve(clip, transcript, hook_strength=0.5)
        silent_points = [p for p in out["curve"] if p["silent"]]
        assert silent_points, "the 3s gap must register as silent seconds"

    def test_stronger_hook_slows_decay(self, segment_transcript):
        clip = {"start": 0.0, "end": 30.0}
        weak = predict_retention_curve(clip, segment_transcript, hook_strength=0.1)
        strong = predict_retention_curve(clip, segment_transcript, hook_strength=0.9)
        assert strong["final_retention"] > weak["final_retention"]

    def test_dropoff_reason_labels(self, segment_transcript):
        out = predict_retention_curve({"start": 0.0, "end": 30.0},
                                      segment_transcript, hook_strength=0.5)
        for d in out["dropoff_points"]:
            assert d["reason"] in ("silence", "low_density", "natural_decay")


# ── Hook Lab ──

class TestHookLab:
    def test_ctr_empty_title(self):
        out = predict_title_ctr("")
        assert out["score"] == 0.0
        assert out["grade"] == "D"

    def test_ctr_power_word_boost(self):
        plain = predict_title_ctr("how to improve your morning routine tips")
        power = predict_title_ctr("the secret morning routine nobody shares")
        assert power["score"] > plain["score"]

    def test_ctr_all_caps_penalty(self):
        caps = predict_title_ctr("THIS IS THE WHOLE TRUTH ABOUT MORNING ROUTINES")
        assert "ALL-CAPS reads as spam" in caps["weaknesses"]

    def test_ctr_number_specificity(self):
        out = predict_title_ctr("7 morning mistakes that ruin your day")
        assert out["factors"]["has_number"] is True

    def test_ctr_vague_penalty(self):
        out = predict_title_ctr("Watch this video about stuff")
        assert any("Vague" in w for w in out["weaknesses"])

    def test_ctr_grade_and_suggestions(self):
        out = predict_title_ctr(
            "This is why millionaires wake at 5AM — the secret nobody shares")
        assert out["grade"] in ("S", "A", "B")
        assert out["suggestions"] or out["strengths"]

    def test_hook_variants_ranked(self, segment_transcript):
        clip = {"start": 0.0, "end": 30.0}
        variants = generate_hook_variants(clip, segment_transcript, n=3)
        assert 1 <= len(variants) <= 3
        assert variants[0]["rank"] == 1
        assert all("archetype" in v and "score" in v for v in variants)
        scores = [v["score"] for v in variants]
        assert scores == sorted(scores, reverse=True)

    def test_hook_variants_invalid_clip(self, segment_transcript):
        variants = generate_hook_variants({"start": "x"}, segment_transcript)
        assert variants == []


# ── Endpoint integration ──

class TestBeyondOpusEndpoints:
    @pytest.fixture()
    def client(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NEXUX_DB_PATH", str(tmp_path / "test.db"))
        monkeypatch.setenv("NEXUX_API_KEY", "")
        from utils.rate_limiter import rate_limiter as rl
        rl._buckets.clear()

        import main
        main.jobs.clear()
        main.cancel_flags.clear()
        main.active_count = 0

        async def fake_process_job(job_id, url, kwargs):
            try:
                main.jobs[job_id]["status"] = "completed"
                main.jobs[job_id]["progress"] = 100
                main._save_job(main.jobs[job_id])
            finally:
                main.active_count = max(0, main.active_count - 1)

        monkeypatch.setattr(main, "_process_job", fake_process_job)

        from fastapi.testclient import TestClient
        with TestClient(main.app) as c:
            yield c

    def _seed_job(self, main_module, job_id="beyond-1"):
        """Write a completed job straight into the env-resolved DB.

        The extras router resolves NEXUX_DB_PATH at call time while main.py's
        connection is bound at import time — seeding via raw sqlite keeps the
        test independent of that module-level binding.
        """
        import os
        import sqlite3
        from datetime import datetime, timezone

        bundle = {
            "clip_candidates": [{"start": 0.0, "end": 8.0}],
            "transcript_segments": [
                {"start": 0.0, "end": 2.0, "text": "The secret nobody shares",
                 "speaker": "SPEAKER_00"},
                {"start": 5.0, "end": 8.0, "text": "about morning routines.",
                 "speaker": "SPEAKER_00"},
            ],
        }
        db_path = os.environ["NEXUX_DB_PATH"]
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, status TEXT NOT NULL DEFAULT 'queued',
                    progress REAL DEFAULT 0.0, stage TEXT DEFAULT 'queued',
                    output_path TEXT, error TEXT, created_at TEXT, updated_at TEXT,
                    clips TEXT, broll INTEGER DEFAULT 0, render_meta TEXT,
                    analysis_bundle TEXT, critique TEXT, revision TEXT,
                    publish_plan TEXT, editorial_decision TEXT,
                    request_data TEXT, api_key_hash TEXT
                )""")
            conn.execute(
                "INSERT OR REPLACE INTO jobs (job_id, status, progress, stage,"
                " created_at, updated_at, clips, render_meta, analysis_bundle)"
                " VALUES (?, 'completed', 100, 'completed', ?, ?, '[]', '[]', ?)",
                (job_id, now, now, json.dumps(bundle)))
            conn.commit()
        finally:
            conn.close()
        return job_id

    def test_retention_endpoint(self, client):
        import main
        jid = self._seed_job(main)
        res = client.get(f"/api/clips/{jid}/0/retention")
        assert res.status_code == 200
        body = res.json()
        assert body["curve"] and body["grade"] in ("S", "A", "B", "C", "D")

    def test_retention_endpoint_out_of_range(self, client):
        import main
        jid = self._seed_job(main)
        assert client.get(f"/api/clips/{jid}/7/retention").status_code == 404

    def test_hook_lab_endpoint(self, client):
        import main
        jid = self._seed_job(main)
        res = client.get(f"/api/clips/{jid}/0/hook-lab")
        assert res.status_code == 200
        body = res.json()
        assert body["count"] >= 1
        assert body["variants"][0]["rank"] == 1

    def test_hook_lab_unknown_job_404(self, client):
        assert client.get("/api/clips/nope/0/hook-lab").status_code == 404

    def test_retention_unknown_job_404(self, client):
        assert client.get("/api/clips/nope/0/retention").status_code == 404
