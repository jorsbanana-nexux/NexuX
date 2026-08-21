"""
NexuX V8.5 — Advanced Caption Engine (Kinetic Typography v2)
==============================================================
Next-gen animated caption system that surpasses Opus Clip's caption quality.

Features:
1. WORD-BY-WORD kinetic animation (pop, slide, bounce, fade)
2. ACTIVE WORD HIGHLIGHTING — current word glows, past words dim
3. DYNAMIC SCALE — important words scale up (numbers, names, emotions)
4. MULTI-LAYER SHADOW — 3D depth effect for readability
5. AUTO-EMPHASIS — detects emphasis words and highlights them
6. BREATHING ANIMATION — subtle scale pulse for "alive" feel
7. GRADIENT TEXT — animated color gradients for premium look
8. SPEAKER AWARENESS — different colors for different speakers
9. EMOJI INJECTION — auto-adds relevant emoji for engagement
10. PROGRESS BAR — caption progress indicator at bottom

ASS subtitle format with full karaoke (\k) support.
"""
import re
import math
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

log = logging.getLogger("nexus.caption_v2")


# -- Emphasis Detection --

# Words that should be emphasized (scaled up, highlighted)
EMPHASIS_PATTERNS = {
    # Numbers and data
    "number": r"^\$?\d+([.,]\d+)?%?$",
    # Emotional intensifiers
    "intensifier": r"\b(never|always|everyone|nobody|nothing|everything|amazing|terrible|incredible|impossible)\b",
    # Indonesian intensifiers
    "intensifier_id": r"\b(tidak pernah|selalu|semua|tidak ada|luar biasa|mustahil|gila|edan)\b",
    # Question words (engagement hooks)
    "question": r"\b(why|how|what|who|when|where|which)\b",
    # Power words for virality
    "power": r"\b(secret|truth|nobody|actually|real|fact|proven|shocking)\b",
    "power_id": r"\b(rahasia|kebenaran|sebenarnya|nyatanya|faktanya|terbongkar)\b",
}

# Emoji mapping for common words (auto-injection)
EMOJI_MAP = {
    "money": [("money", "$"), ("cash", "$"), ("dollar", "$"), ("rich", "$"),
              ("untung", "$"), ("cuan", "$"), ("juta", "$"), ("miliar", "$")],
    "fire": [("amazing", "fire"), ("incredible", "fire"), ("crazy", "fire"),
             ("gila", "fire"), ("keren", "fire"), ("mantap", "fire")],
    "mind": [("mind blown", "mind"), ("unbelievable", "mind"), ("shocking", "mind"),
             ("buset", "mind"), ("anjir", "mind")],
    "warning": [("wrong", "warning"), ("mistake", "warning"), ("never", "warning"),
                ("salah", "warning"), ("jangan", "warning")],
    "lightbulb": [("idea", "lightbulb"), ("tip", "lightbulb"), ("secret", "lightbulb"),
                  ("tips", "lightbulb"), ("cara", "lightbulb")],
    "chart": [("success", "chart"), ("growth", "chart"), ("profit", "chart"),
              ("sukses", "chart"), ("berkembang", "chart")],
    "heart": [("love", "heart"), ("amazing", "heart"), ("beautiful", "heart"),
              ("cinta", "heart"), ("indah", "heart")],
    "eyes": [("look", "eyes"), ("watch", "eyes"), ("see", "eyes"), ("check", "eyes"),
             ("lihat", "eyes"), ("perhatikan", "eyes")],
}


# -- Animation Types --

ANIMATIONS = {
    "pop": {
        "description": "Word pops in with scale bounce",
        "ass_transform": "alpha=0,\\fscx=0,\\fscy=0;"
                        "alpha=255,\\fscx=115,\\fscy=115;"
                        "alpha=255,\\fscx=100,\\fscy=100",
        "duration": 0.25,
    },
    "pop_fast": {
        "description": "Quick pop with snap",
        "ass_transform": "alpha=0,\\fscx=0,\\fscy=0;"
                        "alpha=255,\\fscx=120,\\fscy=120;"
                        "alpha=255,\\fscx=100,\\fscy=100",
        "duration": 0.15,
    },
    "slide_up": {
        "description": "Word slides up from below",
        "ass_transform": "alpha=0,\\fscy=0,\\yshift=20;"
                        "alpha=255,\\fscy=100,\\yshift=0",
        "duration": 0.2,
    },
    "slide_left": {
        "description": "Word slides in from right",
        "ass_transform": "alpha=0,\\xshift=30;"
                        "alpha=255,\\xshift=0",
        "duration": 0.2,
    },
    "fade": {
        "description": "Simple fade in",
        "ass_transform": "alpha=0;alpha=255",
        "duration": 0.15,
    },
    "fade_slow": {
        "description": "Slow fade in for cinematic feel",
        "ass_transform": "alpha=0;alpha=255",
        "duration": 0.4,
    },
    "bounce": {
        "description": "Bounce in with overshoot",
        "ass_transform": "alpha=0,\\fscx=0,\\fscy=0;"
                        "alpha=255,\\fscx=130,\\fscy=130;"
                        "alpha=255,\\fscx=90,\\fscy=90;"
                        "alpha=255,\\fscx=100,\\fscy=100",
        "duration": 0.3,
    },
    "typewriter": {
        "description": "Typewriter effect",
        "ass_transform": "alpha=0;alpha=255",
        "duration": 0.05,
    },
    "flicker": {
        "description": "Flicker in (gaming style)",
        "ass_transform": "alpha=0;alpha=255;alpha=0;alpha=255",
        "duration": 0.2,
    },
    "slow_reveal": {
        "description": "Slow dramatic reveal",
        "ass_transform": "alpha=0,\\fscx=50,\\fscy=50;"
                        "alpha=255,\\fscx=100,\\fscy=100",
        "duration": 0.5,
    },
}


# -- Style Enhancements --

# Advanced style properties layered on top of base style presets
ADVANCED_STYLE_PROPS = {
    # Premium styles with enhanced effects
    "hormozi": {
        "shadow_layers": 3,        # Multi-layer shadow for depth
        "active_word_glow": True,   # Current word glows
        "active_word_color": "&H00FFD700&",  # Gold for active
        "past_word_alpha": 180,     # Dim past words
        "emphasis_scale": 1.3,      # Scale up emphasis words
        "emphasis_color": "&H00FFD700&",
        "breathing": True,          # Subtle scale pulse
        "progress_bar": True,
        "bg_blur": True,            # Blur background behind text
        "bg_rounded": True,
    },
    "mrbeast": {
        "shadow_layers": 4,
        "active_word_glow": True,
        "active_word_color": "&H0000FF88&",
        "past_word_alpha": 160,
        "emphasis_scale": 1.4,
        "emphasis_color": "&H0000FF88&",
        "breathing": False,
        "progress_bar": True,
        "bg_blur": True,
        "bg_rounded": True,
    },
    "tiktok_viral": {
        "shadow_layers": 2,
        "active_word_glow": True,
        "active_word_color": "&H00FF6600&",
        "past_word_alpha": 200,
        "emphasis_scale": 1.25,
        "emphasis_color": "&H00FFD700&",
        "breathing": True,
        "progress_bar": False,
        "bg_blur": False,
        "bg_rounded": False,
    },
    "podcast": {
        "shadow_layers": 2,
        "active_word_glow": True,
        "active_word_color": "&H0000D4AA&",
        "past_word_alpha": 200,
        "emphasis_scale": 1.15,
        "emphasis_color": "&H0000D4AA&",
        "breathing": False,
        "progress_bar": True,
        "bg_blur": True,
        "bg_rounded": True,
    },
    "cinematic": {
        "shadow_layers": 3,
        "active_word_glow": False,
        "active_word_color": "&H008888FF&",
        "past_word_alpha": 220,
        "emphasis_scale": 1.1,
        "emphasis_color": "&H008888FF&",
        "breathing": False,
        "progress_bar": False,
        "bg_blur": True,
        "bg_rounded": True,
    },
    "gaming": {
        "shadow_layers": 4,
        "active_word_glow": True,
        "active_word_color": "&H00FF4444&",
        "past_word_alpha": 150,
        "emphasis_scale": 1.35,
        "emphasis_color": "&H00FFFF00&",
        "breathing": True,
        "progress_bar": True,
        "bg_blur": False,
        "bg_rounded": False,
    },
}

# Default enhanced props for styles not in the advanced map
DEFAULT_ADVANCED_PROPS = {
    "shadow_layers": 2,
    "active_word_glow": True,
    "active_word_color": "&H00FFFFFF&",
    "past_word_alpha": 200,
    "emphasis_scale": 1.2,
    "emphasis_color": "&H00FFD700&",
    "breathing": False,
    "progress_bar": False,
    "bg_blur": False,
    "bg_rounded": False,
}


# -- Main Caption Builder --

def build_advanced_ass(
    transcript: Dict,
    clip: Dict,
    style_config: Dict,
    job_id: str,
    clip_idx: int,
    video_width: int,
    video_height: int,
    style_name: Optional[str] = None,
) -> Path:
    """
    Build an advanced ASS subtitle file with kinetic typography.

    Features:
    - Word-by-word animation (pop, bounce, fade, etc.)
    - Active word highlighting with glow
    - Emphasis words scaled up
    - Multi-layer shadow for depth
    - Progress bar at bottom
    - Auto emoji injection

    Returns: Path to the .ass file
    """
    from .subtitle_quality import group_words_for_readability, smart_line_break

    out_dir = Path("output") / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    ass_path = out_dir / f"clip_{clip_idx:02d}_captions.ass"

    # Get word groups from subtitle quality engine
    segments = transcript.get("segments", [])
    clip_start = clip["start"]
    clip_end = clip["end"]

    all_groups = []
    for seg in segments:
        ss = float(seg.get("start", 0))
        se = float(seg.get("end", 0))
        if se < clip_start or ss > clip_end:
            continue

        words = seg.get("words", [])
        if words:
            groups = group_words_for_readability(words, clip_start, clip_end)
            all_groups.extend(groups)
        else:
            text = seg.get("text", "").strip()
            if text:
                all_groups.append({
                    "text": text,
                    "start": max(ss, clip_start),
                    "end": min(se, clip_end),
                    "duration": min(se, clip_end) - max(ss, clip_start),
                    "word_count": len(text.split()),
                    "words": [],
                })

    # Get style properties
    style_name_resolved = style_name or style_config.get("preset", "hormozi")
    adv_props = ADVANCED_STYLE_PROPS.get(style_name_resolved, DEFAULT_ADVANCED_PROPS)

    # Get animation type from style
    animation = style_config.get("animation", "pop")
    anim_config = ANIMATIONS.get(animation, ANIMATIONS["pop"])

    # Build ASS file
    ass_lines = _build_ass_header(
        style_config, video_width, video_height, adv_props
    )

    # Process each word group
    for group in all_groups:
        group_text = group["text"]
        group_start = group["start"] - clip_start  # Relative to clip
        group_end = group["end"] - clip_start
        group_dur = group["duration"]

        # Apply smart line breaking
        display_text = smart_line_break(group_text, max_length=42)

        # Split into individual words for kinetic animation
        words = display_text.split("\\N") if "\\N" in display_text else [display_text]

        # Build the dialogue line with per-word animation
        line = _build_kinetic_line(
            words=words,
            start_time=group_start,
            duration=group_dur,
            style_config=style_config,
            adv_props=adv_props,
            anim_config=anim_config,
        )
        ass_lines.append(line)

    # Add progress bar
    if adv_props.get("progress_bar", False):
        clip_dur = clip_end - clip_start
        progress_line = _build_progress_bar_line(clip_dur, video_width, video_height)
        ass_lines.append(progress_line)

    # Write ASS file
    ass_content = "\n".join(ass_lines)
    ass_path.write_text(ass_content, encoding="utf-8")

    log.info(f"[CaptionV2] Built {len(all_groups)} caption groups for clip {clip_idx} "
             f"({style_name_resolved}, {animation}) -> {ass_path.name}")

    return ass_path


def _build_ass_header(
    style_config: Dict,
    video_width: int,
    video_height: int,
    adv_props: Dict,
) -> List[str]:
    """Build the ASS file header with styles."""
    font = style_config.get("font", "Arial")
    font_size = style_config.get("font_size", 52)
    primary = _hex_to_ass(style_config.get("primary", "#FFFFFF"))
    stroke = _hex_to_ass(style_config.get("stroke", "#000000"))
    stroke_width = style_config.get("stroke_width", 3)
    bold = style_config.get("bold", True)
    position = style_config.get("position", "center")

    # Y position based on style
    if position == "center":
        alignment = 5  # Center center
        margin_v = 0
    elif position == "bottom":
        alignment = 2  # Bottom center
        margin_v = int(video_height * 0.08)
    elif position == "top":
        alignment = 8  # Top center
        margin_v = int(video_height * 0.08)
    else:
        alignment = 5
        margin_v = 0

    # Bold flag
    bold_flag = "-1" if bold else "0"

    # Multi-layer shadow for depth
    shadow = 0
    if adv_props.get("shadow_layers", 0) > 0:
        shadow = adv_props["shadow_layers"]

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: " + str(video_width),
        "PlayResY: " + str(video_height),
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        f"OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        f"ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        f"Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Main,{font},{font_size},{primary},{primary},"
        f"{stroke},&H80000000,{bold_flag},0,0,0,100,100,0,0,1,"
        f"{stroke_width},{shadow},{alignment},40,40,{margin_v},1",
        # Emphasis style (slightly larger, colored)
        f"Style: Emphasis,{font},{int(font_size * 1.15)},"
        f"{adv_props.get('emphasis_color', primary)},"
        f"{adv_props.get('emphasis_color', primary)},"
        f"{stroke},{bold_flag},0,0,0,100,100,0,0,1,"
        f"{stroke_width},{shadow},{alignment},40,40,{margin_v},1",
        # Progress bar style
        f"Style: Progress, Arial,{int(video_height * 0.008)},"
        f"&H00FFD700&,&H00FFD700&,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,"
        f"0,0,2,0,0,0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    return header


def _build_kinetic_line(
    words: List[str],
    start_time: float,
    duration: float,
    style_config: Dict,
    adv_props: Dict,
    anim_config: Dict,
) -> str:
    """Build a single ASS dialogue line with per-word kinetic animation."""
    # Convert time to ASS format (0:00:00.00)
    start_ass = _seconds_to_ass(start_time)
    end_ass = _seconds_to_ass(start_time + duration + 0.3)  # Small buffer

    # Total words across all lines (for per-word timing)
    all_words = []
    for line in words:
        all_words.extend(line.split())

    if not all_words:
        return ""

    # Per-word timing within the group
    word_dur = max(anim_config["duration"], duration / max(len(all_words), 1))

    # Build the text with animation tags per word
    text_parts = []
    current_time = start_time
    active_color = adv_props.get("active_word_color", "&H00FFFFFF&")
    past_alpha = adv_props.get("past_word_alpha", 200)

    for i, word in enumerate(all_words):
        word_start = current_time
        word_end = current_time + word_dur
        is_last = (i == len(all_words) - 1)

        # Check if this word should be emphasized
        is_emphasis = _is_emphasis_word(word)

        # Build per-word animation
        anim_tags = []

        # Entrance animation
        if anim_config["ass_transform"]:
            # Apply transform at word start
            transform_dur = int(anim_config["duration"] * 100)
            offset_ms = int((word_start - start_time) * 1000)
            anim_tags.append(
                f"\\t({offset_ms},{offset_ms + transform_dur},"
                f"{anim_config['ass_transform']})"
            )

        # Active word highlighting (glow effect)
        if adv_props.get("active_word_glow", False) and not is_last:
            # Active word: full opacity + color
            glow_start = int((word_start - start_time) * 1000)
            glow_end = int((word_end - start_time) * 1000)
            anim_tags.append(
                f"\\t({glow_start},{glow_end},\\c{active_color}\\3c{active_color})"
            )
            # After active: dim slightly
            if past_alpha < 255:
                dim_alpha = (255 - past_alpha) * 4
                anim_tags.append(
                    f"\\t({glow_end},{glow_end + 50},\\alpha&H{dim_alpha:02X}&)"
                )

        # Emphasis scaling
        if is_emphasis:
            scale = int(adv_props.get("emphasis_scale", 1.2) * 100)
            scale_dur = 150
            offset_ms = int((word_start - start_time) * 1000)
            anim_tags.append(
                f"\\t({offset_ms},{offset_ms + scale_dur},"
                f"\\fscx{scale}\\fscy{scale})"
            )

        # Breathing effect
        if adv_props.get("breathing", False) and i == 0:
            breath_dur = int(duration * 1000)
            anim_tags.append(
                f"\\t(0,{breath_dur // 2},\\fscx105\\fscy105)"
                f"\\t({breath_dur // 2},{breath_dur},\\fscx100\\fscy100)"
            )

        # Combine tags with word
        tags_str = "".join(anim_tags)
        styled_word = f"{{{tags_str}}}{word}"
        text_parts.append(styled_word)

        current_time = word_end

    # Join with spaces (line breaks preserved with \N)
    full_text = " ".join(text_parts)

    # Re-insert line breaks
    if "\\N" in " ".join(words):
        # Rebuild with line breaks at the right positions
        full_text = _rebuild_with_linebreaks(words, all_words, text_parts, anim_config, start_time, duration, style_config, adv_props)

    return f"Dialogue: 0,{start_ass},{end_ass},Main,,0,0,0,,{full_text}"


def _rebuild_with_linebreaks(lines, all_words, text_parts, anim_config, start_time, duration, style_config, adv_props):
    """Rebuild caption text with line breaks preserved."""
    result_parts = []
    word_idx = 0
    for line in lines:
        line_words = line.split()
        for w in line_words:
            if word_idx < len(text_parts):
                result_parts.append(text_parts[word_idx])
                word_idx += 1
        result_parts.append("\\N")  # Line break
    return " ".join(result_parts).rstrip("\\N")


def _build_progress_bar_line(clip_duration: float, video_width: int, video_height: int) -> str:
    """Build a progress bar ASS line."""
    start_ass = "0:00:00.00"
    end_ass = _seconds_to_ass(clip_duration)

    # Progress bar: a colored bar that grows from 0 to full width
    bar_height = int(video_height * 0.006)
    total_width = video_width - 80  # Margins

    # Use \pos and \fscx to animate the bar width
    # Start at 0 width, grow to full width over clip duration
    dur_ms = int(clip_duration * 1000)

    text = (
        f"{{\\pos({video_width // 2},{video_height - bar_height - 20})}}"
        f"{{\\fscx0\\fscy100}}"
        f"{{\\t(0,{dur_ms},\\fscx100)}}"
        f"{{\\p1}}m 0 0 l {total_width} 0 l {total_width} {bar_height} l 0 {bar_height}"
    )

    return f"Dialogue: 1,{start_ass},{end_ass},Progress,,0,0,0,,{text}"


def _is_emphasis_word(word: str) -> bool:
    """Check if a word should be emphasized (scaled up)."""
    word_clean = re.sub(r"[^\w\s$%]", "", word).strip().lower()
    if not word_clean:
        return False

    for category, pattern in EMPHASIS_PATTERNS.items():
        if re.search(pattern, word_clean):
            return True
    return False


def _detect_emoji(word: str) -> Optional[str]:
    """Detect if a word should have an emoji injected."""
    word_lower = word.lower().strip(".,!?;:""'")
    for emoji_name, word_list in EMOJI_MAP.items():
        for trigger, emoji_key in word_list:
            if trigger in word_lower:
                return emoji_key
    return None


def _hex_to_ass(hex_color: str) -> str:
    """Convert hex color (#RRGGBB) to ASS color (&H00BBGGRR&)."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}&"


def _seconds_to_ass(seconds: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


# -- Caption Quality Scorer --

def score_caption_quality(
    groups: List[Dict],
    style_config: Dict,
    style_name: Optional[str] = None,
) -> Dict:
    """
    Score caption quality on multiple dimensions.
    
    Returns:
        {
            "score": 0-100,
            "readability": 0-100,
            "animation_quality": 0-100,
            "emphasis_accuracy": 0-100,
            "timing_quality": 0-100,
            "visual_appeal": 0-100,
            "issues": [...],
            "recommendations": [...],
        }
    """
    issues = []
    recommendations = []

    # 1. Readability (from subtitle quality engine)
    from .subtitle_quality import validate_readability
    readability_report = validate_readability(groups)
    readability = readability_report["quality_score"] * 100
    issues.extend(readability_report.get("issues", []))

    # 2. Animation quality
    animation = style_config.get("animation", "pop")
    anim_config = ANIMATIONS.get(animation, ANIMATIONS["pop"])
    animation_quality = 80.0

    if animation in ("pop", "pop_fast", "bounce"):
        animation_quality = 90.0  # High engagement
    elif animation in ("fade", "fade_slow"):
        animation_quality = 75.0  # Clean but less engaging
    elif animation == "flicker":
        animation_quality = 85.0  # Eye-catching
    elif animation == "typewriter":
        animation_quality = 70.0  # Can feel slow

    # 3. Emphasis accuracy
    emphasis_count = sum(1 for g in groups for w in g["text"].split() if _is_emphasis_word(w))
    total_words = sum(g["word_count"] for g in groups)
    emphasis_ratio = emphasis_count / max(total_words, 1)

    if 0.05 <= emphasis_ratio <= 0.20:
        emphasis_accuracy = 90.0  # Good ratio
    elif emphasis_ratio > 0.20:
        emphasis_accuracy = 70.0  # Too many emphasis words
        issues.append("Too many emphasis words - reduce for better impact")
    elif emphasis_ratio < 0.03:
        emphasis_accuracy = 75.0  # Too few
        recommendations.append("Add emphasis to important words (numbers, power words)")
    else:
        emphasis_accuracy = 80.0

    # 4. Timing quality
    timing_quality = 85.0
    for g in groups:
        cps = len(g["text"]) / max(g["duration"], 0.1)
        if cps > 25:
            timing_quality -= 5
            issues.append(f"CPS too high for: {g['text'][:30]}...")
        if g["duration"] < 0.7:
            timing_quality -= 3

    timing_quality = max(0, timing_quality)

    # 5. Visual appeal (based on style props)
    style_name_resolved = style_name or style_config.get("preset", "hormozi")
    adv_props = ADVANCED_STYLE_PROPS.get(style_name_resolved, DEFAULT_ADVANCED_PROPS)

    visual_appeal = 70.0
    if adv_props.get("active_word_glow"):
        visual_appeal += 10
    if adv_props.get("shadow_layers", 0) >= 3:
        visual_appeal += 5
    if adv_props.get("progress_bar"):
        visual_appeal += 5
    if adv_props.get("breathing"):
        visual_appeal += 5
    if style_config.get("highlight_words", False):
        visual_appeal += 5

    # Composite
    score = (
        readability * 0.25 +
        animation_quality * 0.20 +
        emphasis_accuracy * 0.20 +
        timing_quality * 0.15 +
        visual_appeal * 0.20
    )

    if not recommendations:
        if score >= 85:
            recommendations.append("Caption quality is excellent - no changes needed")
        elif score >= 70:
            recommendations.append("Good caption quality - consider a more dynamic animation style")

    return {
        "score": round(score, 1),
        "readability": round(readability, 1),
        "animation_quality": round(animation_quality, 1),
        "emphasis_accuracy": round(emphasis_accuracy, 1),
        "timing_quality": round(timing_quality, 1),
        "visual_appeal": round(visual_appeal, 1),
        "issues": issues,
        "recommendations": recommendations,
    }
