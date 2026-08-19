"""
NexuX V8.0 — Constants & Configuration
=======================================================
All tunable parameters, aspect ratios, codec presets,
style definitions, and keyword databases.
"""
from pathlib import Path
import os
import tempfile

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.environ.get("NEXUS_OUTPUT_DIR", str(BASE_DIR / "output")))
ASSETS_DIR = Path(os.environ.get("NEXUS_ASSETS_DIR", str(BASE_DIR / "assets")))
TEMP_DIR = Path(tempfile.gettempdir()) / "nexus-clipper-premium"

for d in [OUTPUT_DIR, ASSETS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Pipeline ───────────────────────────────────────────
MAX_RETRIES = 3
DOWNLOAD_TIMEOUT = 600
RENDER_TIMEOUT = 1200
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "3"))
JOB_TIMEOUT_MINUTES = int(os.environ.get("JOB_TIMEOUT_MINUTES", "30"))

# ── Aspect Ratios (width, height) ─────────────────────
ASPECT_RATIOS = {
    "9:16":  (1080, 1920),   # TikTok, Reels, Shorts
    "1:1":   (1080, 1080),   # Instagram Square
    "16:9":  (1920, 1080),   # YouTube Landscape
    "4:5":   (1080, 1350),   # Instagram Portrait
    "2:3":   (1080, 1620),   # Pinterest
    "21:9":  (1920, 822),    # Cinematic Wide
    "3:4":   (1080, 1440),   # Facebook Feed
}

# ── Video Codecs ───────────────────────────────────────
VIDEO_CODECS = {
    "h264":  {"codec": "libx264",  "crf": "23", "preset": "medium"},
    "h265":  {"codec": "libx265",  "crf": "28", "preset": "medium"},
    "vp9":   {"codec": "libvpx-vp9", "crf": "30", "preset": "good"},
    "av1":   {"codec": "libsvtav1",  "crf": "30", "preset": "8"},
}

AUDIO_CODECS = {
    "aac":  {"codec": "aac",        "bitrate": "192k"},
    "mp3":  {"codec": "libmp3lame", "bitrate": "192k"},
    "opus": {"codec": "libopus",    "bitrate": "128k"},
}

# ── Color Grading Presets ─────────────────────────────
COLOR_GRADES = {
    "none":       "",
    "warm":       "eq=saturation=1.15:brightness=0.03:gamma=1.05",
    "cool":       "eq=saturation=0.90:brightness=-0.02:gamma=0.95",
    "vibrant":    "eq=saturation=1.35:contrast=1.10:brightness=0.04",
    "cinematic":  "eq=saturation=0.82:contrast=1.15:brightness=-0.04:gamma=1.02",
    "noir":       "eq=saturation=0.0:contrast=1.30:brightness=-0.08",
    "vintage":    "eq=saturation=0.75:contrast=1.05:brightness=0.02:gamma=1.10",
    "hdr_pop":    "eq=saturation=1.50:contrast=1.25:brightness=0.06:gamma=0.95",
}

# ── Viral Scoring ─────────────────────────────────────
EXCITEMENT_KEYWORDS = [
    # English
    "wow", "amazing", "incredible", "crazy", "secret", "never", "shocking",
    "unbelievable", "insane", "game changer", "mind-blowing", "exposed",
    "breakthrough", "revolutionary", "conspiracy", "hidden truth",
    "what if", "the real reason", "nobody knows", "they don't want you to know",
    "plot twist", "you won't believe", "this happened", "changed everything",
    "life changing", "million dollars", "worst mistake", "number one",
    # Indonesian
    "mengerikan", "rahasia", "gila", "aneh", "menakjubkan", "viral",
    "fenomenal", "terbongkar", "fakta", "misteri", "ternyata", "buset",
    "anjir", "edan", "nggak nyangka", "membongkar", "terkuak",
    "nggak ada yang tahu", "selama ini bohong", "akhirnya terbukti",
    # Spanish
    "increíble", "secreto", "loco", "impactante", "nadie sabe",
    "revelado", "expuesto", "millonario",
]

HOOK_PATTERNS = [
    # Pattern (regex-like substring), score_bonus
    ("stop scrolling", 8),
    ("you won't believe", 10),
    ("the truth about", 9),
    ("nobody talks about", 8),
    ("what if i told you", 9),
    ("this is why", 6),
    ("the secret", 7),
    ("they don't want you to know", 10),
    ("i found something", 8),
    ("this changed everything", 9),
    ("wait for it", 7),
    ("watch till the end", 6),
    ("storytime", 5),
    ("don't skip", 6),
    ("here's the thing", 5),
    ("ternyata selama ini", 8),
    ("rahasia yang tidak", 9),
    ("terkuak sudah", 8),
    ("nggak ada yang ngasih tahu", 9),
    ("akhirnya ketahuan", 8),
]

# ── Retention Anchors (keep viewers watching) ─────────
RETENTION_TRIGGERS = {
    "visual_change": {"score": 3, "description": "Visual change every 2-3 seconds"},
    "text_pop":      {"score": 5, "description": "Pop-up text overlay"},
    "zoom_effect":   {"score": 4, "description": "Ken Burns / zoom effect"},
    "sound_effect":  {"score": 3, "description": "SFX sting"},
    "color_flash":   {"score": 2, "description": "Brief color change"},
    "speed_ramp":    {"score": 4, "description": "Speed up / slow down"},
    "question":      {"score": 6, "description": "Rhetorical question"},
    "number":        {"score": 3, "description": "List / numbered point"},
    "contrast":      {"score": 4, "description": "Before/after or comparison"},
}

# ── Transition Types ──────────────────────────────────
TRANSITIONS = {
    "hard_cut":     "",
    "fade":         "fade=t=out:st={start}:d={dur},fade=t=in:st={start}:d={dur}",
    "dissolve":     "",
    "wipe_left":    "",
    "slide_up":     "",
    "zoom_in":      "",
    "glitch":       "",
}

# ── B-Roll Configuration ──────────────────────────────
BROLL_DEFAULT_ENABLED = False
BROLL_DEFAULT_INTENSITY = "moderate"
BROLL_DEFAULT_SOURCE = "local"
BROLL_DEFAULT_MODE = "cutaway"
BROLL_DEFAULT_TRANSITION = "fade"

BROLL_INTENSITIES = {
    "subtle": {
        "max_overlays": 1,
        "duration_range": (2.0, 3.0),
        "min_interval": 12.0,
        "description": "Brief, infrequent B-roll overlays",
    },
    "moderate": {
        "max_overlays": 3,
        "duration_range": (3.0, 4.0),
        "min_interval": 7.0,
        "description": "Balanced B-roll cutaways during key moments",
    },
    "aggressive": {
        "max_overlays": 6,
        "duration_range": (3.5, 5.0),
        "min_interval": 4.0,
        "description": "Frequent, dynamic B-roll transitions",
    },
}

BROLL_OVERLAY_MODES = ["cutaway", "picture_in_picture", "split_screen"]
BROLL_SOURCES = ["local", "unsplash", "pexels"]
BROLL_TRANSITIONS = ["fade", "dissolve", "none"]

BROLL_DIR = ASSETS_DIR / "broll"
BROLL_DIR.mkdir(parents=True, exist_ok=True)

UNSPLASH_API_KEY = os.environ.get("UNSPLASH_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
