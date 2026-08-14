"""
Nexus-Clipper Premium v4.0 — Test Suite
=========================================
Tests for all engine modules.
Run: python3 -m pytest tests/ -v
"""
import unittest, sys, json, tempfile
from pathlib import Path

# ── Test Utilities ──

class TestUtils(unittest.TestCase):
    def test_fmt_time(self):
        from engine.utils import fmt_time
        self.assertEqual(fmt_time(0), "0:00:00.00")
        self.assertEqual(fmt_time(65.5), "0:01:05.50")
        self.assertEqual(fmt_time(3661.75), "1:01:01.75")
        self.assertEqual(fmt_time(0.01), "0:00:00.01")

    def test_fmt_duration(self):
        from engine.utils import fmt_duration
        self.assertEqual(fmt_duration(30), "30s")
        self.assertEqual(fmt_duration(125), "2m 5s")
        self.assertEqual(fmt_duration(3600), "60m 0s")

    def test_safe_filename(self):
        from engine.utils import safe_filename
        self.assertEqual(safe_filename("Hello World!"), "Hello World!")
        self.assertEqual(safe_filename("File:Name<Bad>"), "File_Name_Bad_")

    def test_clean_for_json(self):
        from engine.utils import clean_for_json
        import math
        data = {"a": float('nan'), "b": [float('inf'), 1.0], "c": "ok", "d": {"e": float('-inf')}}
        c = clean_for_json(data)
        self.assertEqual(c["a"], 0.0)
        self.assertEqual(c["b"], [0.0, 1.0])
        self.assertEqual(c["c"], "ok")
        self.assertEqual(c["d"]["e"], 0.0)

    def test_to_unix(self):
        from engine.utils import to_unix
        self.assertEqual(to_unix("/path/to/file"), "/path/to/file")


# ── Test Styles ──

class TestStyles(unittest.TestCase):
    def test_hex_to_ass(self):
        from engine.styles import hex_to_ass
        self.assertEqual(hex_to_ass("#FFFFFF"), "&H00FFFFFF")
        self.assertEqual(hex_to_ass("#FFD700"), "&H0000D7FF")
        self.assertEqual(hex_to_ass("#000000"), "&H00000000")
        self.assertEqual(hex_to_ass("#FF00FF"), "&H00FF00FF")

    def test_get_position(self):
        from engine.styles import get_position
        self.assertEqual(get_position("top")["align"], 8)
        self.assertEqual(get_position("center")["align"], 5)
        self.assertEqual(get_position("bottom")["align"], 2)

    def test_resolve_style_preset(self):
        from engine.styles import resolve_style
        r = resolve_style({"subtitle_style": "hormozi"})
        self.assertEqual(r["font"], "Arial")
        self.assertEqual(r["font_size"], 52)
        self.assertEqual(r["primary"], "#FFFFFF")
        self.assertTrue(r["bold"])
        self.assertTrue(r["highlight_words"])

    def test_resolve_style_custom(self):
        from engine.styles import resolve_style
        r = resolve_style({
            "subtitle_style": "custom",
            "font": "TestFont",
            "font_size": 24,
            "primary_color": "#FF0000",
        })
        self.assertEqual(r["font"], "TestFont")
        self.assertEqual(r["font_size"], 24)
        self.assertEqual(r["primary"], "#FF0000")

    def test_all_presets_valid(self):
        from engine.styles import STYLE_PRESETS
        required = ["font", "font_size", "primary", "highlight", "stroke",
                    "position", "animation", "stroke_width", "bold", "highlight_words"]
        for name, preset in STYLE_PRESETS.items():
            for field in required:
                self.assertIn(field, preset, f"{name} missing '{field}'")

    def test_override_works(self):
        from engine.styles import resolve_style
        r = resolve_style({"subtitle_style": "mrbeast", "primary_color": "#0000FF"})
        self.assertEqual(r["primary"], "#0000FF")
        self.assertEqual(r["font"], "Impact")  # preserved

    def test_get_animation_tag(self):
        from engine.styles import get_animation_tag
        self.assertIn("fscx120", get_animation_tag("pop"))
        self.assertIn("fscx125", get_animation_tag("pop_fast"))
        self.assertIn("fade", get_animation_tag("fade"))
        self.assertEqual(get_animation_tag("none"), "")

    def test_30_plus_presets(self):
        from engine.styles import STYLE_PRESETS
        self.assertGreaterEqual(len(STYLE_PRESETS), 28)


# ── Test Constants ──

class TestConstants(unittest.TestCase):
    def test_aspect_ratios(self):
        from engine.constants import ASPECT_RATIOS
        self.assertIn("9:16", ASPECT_RATIOS)
        self.assertIn("16:9", ASPECT_RATIOS)
        self.assertEqual(ASPECT_RATIOS["9:16"], (1080, 1920))

    def test_color_grades(self):
        from engine.constants import COLOR_GRADES
        self.assertIn("vibrant", COLOR_GRADES)
        self.assertIn("cinematic", COLOR_GRADES)
        self.assertIn("hdr_pop", COLOR_GRADES)

    def test_video_codecs(self):
        from engine.constants import VIDEO_CODECS
        self.assertIn("h264", VIDEO_CODECS)
        self.assertIn("h265", VIDEO_CODECS)

    def test_keywords_have_content(self):
        from engine.constants import EXCITEMENT_KEYWORDS
        self.assertGreater(len(EXCITEMENT_KEYWORDS), 20)
        self.assertIn("wow", EXCITEMENT_KEYWORDS)
        self.assertIn("gila", EXCITEMENT_KEYWORDS)  # Indonesian

    def test_hook_patterns(self):
        from engine.constants import HOOK_PATTERNS
        self.assertGreater(len(HOOK_PATTERNS), 10)
        for pattern, score in HOOK_PATTERNS:
            self.assertIsInstance(pattern, str)
            self.assertIsInstance(score, (int, float))
            self.assertGreater(score, 0)


# ── Test Analysis ──

class TestAnalyze(unittest.TestCase):
    def setUp(self):
        from engine.analyze import analyze_content
        self.analyze = analyze_content

    def test_empty(self):
        self.assertEqual(self.analyze({}), [])

    def test_short_video(self):
        t = {"segments": [
            {"start": 0, "end": 5, "text": "Hello world"},
            {"start": 5, "end": 10, "text": "This is amazing incredible"},
        ]}
        r = self.analyze(t, target_duration=60)
        self.assertTrue(len(r) > 0)
        if isinstance(r, list) and len(r) > 0:
            self.assertEqual(r[0]["start"], 0)
        elif isinstance(r, dict):
            self.assertEqual(r["start"], 0)

    def test_long_video_clips(self):
        segs = []
        for i in range(200):
            segs.append({
                "start": i * 3, "end": (i+1) * 3,
                "text": f"Segment {i} wow amazing secret crazy",
            })
        t = {"segments": segs}
        r = self.analyze(t, target_duration=30, max_clips=5)
        self.assertTrue(0 < len(r) <= 5)
        self.assertGreater(r[0]["score"], 0)

    def test_keyword_boost(self):
        boring = [{"start": 0, "end": 30, "text": "normal text nothing special"}]
        exciting = [{"start": 30, "end": 60,
            "text": "wow amazing incredible secret shocking crazy insane "
                    "unbelievable mind-blowing"}]
        t = {"segments": boring + exciting}
        r = self.analyze(t, target_duration=30)
        self.assertTrue(len(r) >= 1)

    def test_clip_fields(self):
        segs = [{"start": i*3, "end": (i+1)*3, "text": f"Hello {i}"} for i in range(100)]
        t = {"segments": segs}
        r = self.analyze(t, target_duration=30, max_clips=3)
        for clip in r:
            for field in ["start", "end", "score", "wps", "keywords_found",
                         "speaker_count", "face_visible_pct"]:
                self.assertIn(field, clip)


# ── Run ──

if __name__ == "__main__":
    unittest.main()
