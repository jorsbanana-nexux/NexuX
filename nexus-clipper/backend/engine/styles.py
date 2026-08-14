"""
Nexus-Clipper Premium v4.0 — Style System
==========================================
30+ subtitle style presets with full kinetic typography support.
Each preset defines: font, size, colors, animation, position, stroke.
"""
from typing import Dict, Any

# Speaker color palette (12 distinct colors)
SPEAKER_PALETTE = [
    "#FFFFFF", "#FFD700", "#00FF88", "#FF6B6B",
    "#82B1FF", "#E040FB", "#FF9100", "#00E5FF",
    "#FF4081", "#B2FF59", "#7C4DFF", "#FFD740",
]

STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    # ── Professional / Business ──
    "hormozi": {
        "font": "Arial", "font_size": 52,
        "primary": "#FFFFFF", "highlight": "#FFD700", "stroke": "#000000",
        "position": "center", "animation": "pop", "stroke_width": 3,
        "bold": True, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.35,
    },
    "iki": {
        "font": "Montserrat", "font_size": 46,
        "primary": "#FFFFFF", "highlight": "#00D4AA", "stroke": "#000000",
        "position": "center", "animation": "pop_fast", "stroke_width": 3,
        "bold": True, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.40,
    },
    "alex_hormozi_v2": {
        "font": "Arial Black", "font_size": 54,
        "primary": "#FFFFFF", "highlight": "#FFD700", "stroke": "#0A0A0A",
        "position": "center", "animation": "pop", "stroke_width": 5,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": True, "bg_opacity": 0.30,
    },

    # ── Entertainment / Viral ──
    "mrbeast": {
        "font": "Impact", "font_size": 56,
        "primary": "#FFFFFF", "highlight": "#00FF88", "stroke": "#000000",
        "position": "center", "animation": "pop_fast", "stroke_width": 6,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "mrbeast_v2": {
        "font": "Anton", "font_size": 58,
        "primary": "#FFFFFF", "highlight": "#FF4444", "stroke": "#000000",
        "position": "center", "animation": "bounce", "stroke_width": 7,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "tiktok_viral": {
        "font": "Arial", "font_size": 50,
        "primary": "#FF6600", "highlight": "#FFD700", "stroke": "#000000",
        "position": "random", "animation": "pop", "stroke_width": 4,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "tiktok_v2": {
        "font": "Proxima Nova", "font_size": 48,
        "primary": "#FFFFFF", "highlight": "#FF0050", "stroke": "#0A0A2E",
        "position": "center", "animation": "bounce", "stroke_width": 4,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": True, "bg_opacity": 0.25,
    },
    "comedy": {
        "font": "Comic Sans MS", "font_size": 48,
        "primary": "#FFCC00", "highlight": "#FF6600", "stroke": "#000000",
        "position": "center", "animation": "bounce", "stroke_width": 3,
        "bold": True, "highlight_words": True, "shadow": False,
        "bg_bar": False, "bg_opacity": 0.0,
    },

    # ── Gaming ──
    "gaming": {
        "font": "Impact", "font_size": 58,
        "primary": "#FF4444", "highlight": "#FFFF00", "stroke": "#000000",
        "position": "center", "animation": "bounce", "stroke_width": 5,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "gaming_esports": {
        "font": "Industry", "font_size": 56,
        "primary": "#00FF88", "highlight": "#FFFFFF", "stroke": "#0A0A2E",
        "position": "center", "animation": "flicker", "stroke_width": 4,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "gaming_horror": {
        "font": "Impact", "font_size": 54,
        "primary": "#FF0000", "highlight": "#FF6666", "stroke": "#1A0000",
        "position": "center", "animation": "flicker", "stroke_width": 6,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },

    # ── Cinematic / Film ──
    "cinematic": {
        "font": "Georgia", "font_size": 44,
        "primary": "#EEEEFF", "highlight": "#8888FF", "stroke": "#000011",
        "position": "bottom", "animation": "fade_slow", "stroke_width": 4,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.50,
    },
    "cinematic_gold": {
        "font": "Times New Roman", "font_size": 46,
        "primary": "#FFD700", "highlight": "#FFF8DC", "stroke": "#1A1A00",
        "position": "bottom", "animation": "fade_slow", "stroke_width": 3,
        "bold": False, "highlight_words": False, "shadow": True,
        "bg_bar": True, "bg_opacity": 0.55,
    },

    # ── Documentary / Education ──
    "documentary": {
        "font": "Georgia", "font_size": 38,
        "primary": "#DDCCAA", "highlight": "#FFEEDD", "stroke": "#1A1A0A",
        "position": "bottom", "animation": "fade_slow", "stroke_width": 2,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.60,
    },
    "educational": {
        "font": "Verdana", "font_size": 40,
        "primary": "#66BBFF", "highlight": "#FFD700", "stroke": "#0D47A1",
        "position": "top", "animation": "fade", "stroke_width": 2,
        "bold": False, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.40,
    },
    "tutorial": {
        "font": "Segoe UI", "font_size": 36,
        "primary": "#FFFFFF", "highlight": "#00D4AA", "stroke": "#1A1A2E",
        "position": "bottom", "animation": "none", "stroke_width": 2,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.50,
    },

    # ── Podcast ──
    "podcast": {
        "font": "Helvetica", "font_size": 38,
        "primary": "#FFFFFF", "highlight": "#00D4AA", "stroke": "#0A0A2E",
        "position": "bottom", "animation": "fade", "stroke_width": 3,
        "bold": False, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.45,
    },
    "podcast_dynamic": {
        "font": "Inter", "font_size": 40,
        "primary": "#FFFFFF", "highlight": "#FF6B6B", "stroke": "#1A1A2E",
        "position": "center", "animation": "pop", "stroke_width": 3,
        "bold": True, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.35,
    },

    # ── Aesthetic / Minimal ──
    "minimalist": {
        "font": "Helvetica", "font_size": 34,
        "primary": "#CCCCCC", "highlight": "#FFFFFF", "stroke": "#000000",
        "position": "bottom", "animation": "none", "stroke_width": 1,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "neon": {
        "font": "Arial", "font_size": 48,
        "primary": "#FF00FF", "highlight": "#00FFFF", "stroke": "#4A0072",
        "position": "center", "animation": "flicker", "stroke_width": 3,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "glitch": {
        "font": "Courier New", "font_size": 44,
        "primary": "#00FF00", "highlight": "#00FF88", "stroke": "#003300",
        "position": "center", "animation": "flicker", "stroke_width": 2,
        "bold": False, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "aesthetic": {
        "font": "Helvetica Neue", "font_size": 32,
        "primary": "#FFE4E1", "highlight": "#FFB6C1", "stroke": "#2E1A1A",
        "position": "center", "animation": "fade_slow", "stroke_width": 2,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": False, "bg_opacity": 0.0,
    },

    # ── Emotional ──
    "horror": {
        "font": "Impact", "font_size": 52,
        "primary": "#FF0000", "highlight": "#FF4444", "stroke": "#330000",
        "position": "center", "animation": "flicker", "stroke_width": 5,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "motivational": {
        "font": "Helvetica", "font_size": 46,
        "primary": "#FFFFFF", "highlight": "#EEEEEE", "stroke": "#000000",
        "position": "center", "animation": "slow_reveal", "stroke_width": 3,
        "bold": True, "highlight_words": False, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "emotional": {
        "font": "Georgia", "font_size": 40,
        "primary": "#FFFFFF", "highlight": "#FFB6C1", "stroke": "#1A1A1A",
        "position": "center", "animation": "fade_slow", "stroke_width": 3,
        "bold": False, "highlight_words": True, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.40,
    },

    # ── Retro ──
    "typewriter": {
        "font": "Courier New", "font_size": 44,
        "primary": "#88FF88", "highlight": "#AAFFAA", "stroke": "#003300",
        "position": "bottom", "animation": "typewriter", "stroke_width": 2,
        "bold": False, "highlight_words": False, "shadow": False,
        "bg_bar": True, "bg_opacity": 0.50,
    },
    "80s_retro": {
        "font": "Arial", "font_size": 50,
        "primary": "#FF00FF", "highlight": "#00FFFF", "stroke": "#1A0040",
        "position": "center", "animation": "flicker", "stroke_width": 4,
        "bold": True, "highlight_words": True, "shadow": True,
        "bg_bar": False, "bg_opacity": 0.0,
    },
    "vhs": {
        "font": "Courier New", "font_size": 38,
        "primary": "#FFEE88", "highlight": "#FFCC00", "stroke": "#2A1A00",
        "position": "bottom", "animation": "flicker", "stroke_width": 3,
        "bold": False, "highlight_words": False, "shadow": True,
        "bg_bar": True, "bg_opacity": 0.55,
    },

    # ── Custom (user-defined) ──
    "custom": {
        "font": None, "font_size": None,
        "primary": None, "highlight": None, "stroke": None,
        "position": None, "animation": None, "stroke_width": None,
        "bold": None, "highlight_words": None, "shadow": None,
        "bg_bar": None, "bg_opacity": None,
    },
}

# Animation tag generators (ASS override tags)
ANIMATION_TAGS = {
    "pop":          "{\\t(0,100,\\fscx120\\fscy120)\\t(100,200,\\fscx100\\fscy100)}",
    "pop_fast":     "{\\t(0,65,\\fscx125\\fscy125)\\t(65,130,\\fscx100\\fscy100)}",
    "pop_strong":   "{\\t(0,60,\\fscx135\\fscy135)\\t(60,120,\\fscx90\\fscy90)\\t(120,180,\\fscx100\\fscy100)}",
    "fade":         "{\\fade(100,100)}",
    "fade_slow":    "{\\fade(400,400)}",
    "fade_fast":    "{\\fade(50,50)}",
    "bounce":       "{\\t(0,80,\\fscx130\\fscy130)\\t(80,150,\\fscx85\\fscy85)\\t(150,200,\\fscx100\\fscy100)}",
    "flicker":      "{\\t(0,50,\\alpha&HFF&)\\t(50,100,\\alpha&H00&)\\t(100,130,\\alpha&H80&)\\t(130,160,\\alpha&H00&)}",
    "slow_reveal":  "{\\fade(600,600)}",
    "none":         "",
}

# Position -> ASS alignment + margin
POSITIONS = {
    "top":     {"align": 8, "marv": 60},
    "center":  {"align": 5, "marv": 40},
    "bottom":  {"align": 2, "marv": 80},
    "random":  None,  # resolved at runtime
}


def resolve_style(style_config: dict) -> dict:
    """Merge user config with style preset. Custom mode takes all from config."""
    stype = style_config.get("subtitle_style", "hormozi")
    preset = STYLE_PRESETS.get(stype, STYLE_PRESETS["hormozi"])

    if stype == "custom":
        return {
            "font": style_config.get("font", "Arial"),
            "font_size": style_config.get("font_size", 48),
            "primary": style_config.get("primary_color", "#FFFFFF"),
            "highlight": style_config.get("highlight_color", "#FFD700"),
            "stroke": style_config.get("stroke_color", "#000000"),
            "position": style_config.get("position", "center"),
            "animation": style_config.get("animation", "pop"),
            "stroke_width": style_config.get("stroke_width", 3),
            "bold": style_config.get("bold", True),
            "highlight_words": style_config.get("highlight_active_word", True),
            "shadow": style_config.get("shadow", False),
            "bg_bar": style_config.get("bg_bar", True),
            "bg_opacity": style_config.get("bg_opacity", 0.35),
        }

    # Start from preset, override with user config
    result = dict(preset)
    overrides = [
        ("font", "font"), ("font_size", "font_size"),
        ("primary", "primary_color"), ("highlight", "highlight_color"),
        ("stroke", "stroke_color"), ("position", "position"),
        ("animation", "animation"), ("stroke_width", "stroke_width"),
        ("bold", "bold"), ("highlight_words", "highlight_active_word"),
        ("shadow", "shadow"), ("bg_bar", "bg_bar"),
        ("bg_opacity", "bg_opacity"),
    ]
    for pk, ck in overrides:
        if ck in style_config and style_config[ck] is not None:
            result[pk] = style_config[ck]
    return result


def get_animation_tag(anim_type: str, word_index: int = 0) -> str:
    """Generate ASS animation override tag."""
    tag = ANIMATION_TAGS.get(anim_type, "")
    if anim_type == "typewriter":
        delay = word_index * 50 + 100
        return f"{{\\fade({delay},{delay})}}"
    return tag


def get_position(pos: str, _w: int = 1080, _h: int = 1920) -> dict:
    """Get ASS position config. 'random' picks randomly."""
    import random
    if pos == "random":
        pos = random.choice(["top", "center", "bottom"])
    return POSITIONS.get(pos, POSITIONS["center"])


def hex_to_ass(hex_color: str) -> str:
    """Convert #RRGGBB to ASS &HAABBGGRR format."""
    h = hex_color.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}"
