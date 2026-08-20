"""
NexuX V9.5 — Mode Router (Unified Mode Selection)
====================================================
Clean routing between Mode 1 (Podcast) and Mode 2 (AI Creative).

Mode 1 — Podcast: YouTube URL → clip into viral shorts
  - Podcast analyzer (topic segmentation, punchlines, heat detection)
  - Opus Killer scoring (8-dimension analysis)
  - Clip titler (auto-generate viral titles)
  - Hook detection + shift optimization
  - Critic revision loop

Mode 2 — AI Creative: Keyword → search → compile → narrate
  - Keyword expansion (synonyms, trending, questions)
  - Multi-source YouTube search
  - LLM narrative generation
  - TTS narration + SFX + transitions
  - Auto hashtags + SEO description

This router replaces the scattered mode logic in main.py with one clean entry point.
"""
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass

log = logging.getLogger("nexus.mode_router")


@dataclass
class ModeConfig:
    """Configuration for a mode."""
    mode: str
    name: str
    description: str
    icon: str  # emoji for UI
    color: str  # gradient for UI
    requires_url: bool
    requires_keyword: bool
    features: list


MODE_1_CONFIG = ModeConfig(
    mode="podcast",
    name="Podcast Mode",
    description="Ambil video YouTube panjang (podcast, wawancara, talk show) → potong jadi klip viral pendek. 100% lokal, zero biaya cloud.",
    icon="🎙️",
    color="from-blue-500 to-cyan-500",
    requires_url=True,
    requires_keyword=False,
    features=[
        "Podcast topic segmentation",
        "Punchline extraction",
        "Heat & conflict detection",
        "Speaker diarization",
        "Hook detection (8 archetypes)",
        "Opus Killer scoring (8 dimensions)",
        "Editorial critic with revision loop",
        "Auto-generated viral titles",
        "Filler word removal",
        "Face tracking + auto reframe",
        "B-roll free (authenticity preserved)",
        "Smart zoom + captions + effects",
    ],
)

MODE_2_CONFIG = ModeConfig(
    mode="creative",
    name="AI Creative Mode",
    description="Ketik satu keyword → AI cari 10 video YouTube, ambil momen terbaik, generate narasi, compile jadi satu video viral. Bukan clipper — ini creative compilation engine.",
    icon="✨",
    color="from-purple-500 to-pink-500",
    requires_url=False,
    requires_keyword=True,
    features=[
        "Keyword expansion (synonyms + trending + questions)",
        "Multi-source YouTube search (10+ videos)",
        "Partial download (hanya momen relevan)",
        "LLM narrative generation (hook → build → payoff)",
        "TTS narration (Indonesian + English voices)",
        "SFX + background music",
        "Text overlays + transitions",
        "Auto thumbnail generation",
        "Auto hashtags + SEO title + description",
        "Multi-language support",
        "Smart zoom + color grading per segment",
    ],
)


def get_mode_config(mode: str) -> ModeConfig:
    """Get configuration for a specific mode."""
    if mode == "podcast" or mode == "mode1" or mode == "1":
        return MODE_1_CONFIG
    elif mode == "creative" or mode == "mode2" or mode == "2":
        return MODE_2_CONFIG
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'podcast' or 'creative'.")


def get_all_modes() -> list:
    """Get all available modes for UI display."""
    return [MODE_1_CONFIG, MODE_2_CONFIG]


def validate_mode_input(mode: str, youtube_url: str = None, keyword: str = None) -> tuple:
    """
    Validate that the input matches the selected mode.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    config = get_mode_config(mode)
    
    if config.requires_url and not youtube_url:
        return False, f"{config.name} requires a YouTube URL"
    
    if config.requires_keyword and not keyword:
        return False, f"{config.name} requires a keyword"
    
    if config.requires_url and youtube_url:
        if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
            return False, "URL must be a YouTube link"
    
    return True, ""
