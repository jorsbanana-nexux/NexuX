"""
NexuX V8.0 — Engine Package
============================================
Modular architecture:
- constants.py: All configurations & presets
- styles.py:    30+ subtitle style system
- utils.py:     Path/FFmpeg/retry helpers
- download.py:  yt-dlp video download
- transcribe.py: WhisperX/Whisper transcription
- vision.py:    Face detection, scene analysis, screen detection
- analyze.py:   Viral scoring with AI semantic analysis
- render.py:    FFmpeg rendering with ASS subtitles
- voiceover.py: Edge-TTS synthesis & audio mixing
- pipeline.py:  End-to-end orchestration
- vision_quality.py: Render QA & visual quality assessment
"""
from .constants import *
from .styles import STYLE_PRESETS, resolve_style
from .utils import retry, has_gpu, get_device
from .download import download_youtube, get_video_info, search_youtube
from .transcribe import transcribe as transcribe_video
from .vision import analyze_faces, detect_scene_changes, detect_screen_share
from .vision_quality import visual_quality, inspect_render, media_stream_summary
from .analyze import analyze_content, batch_analyze_with_ai
from .render import render_clip, concatenate_clips, mix_bgm, normalize_audio
from .voiceover import (
    get_available_voices, resolve_voice_id, speed_to_edge_rate,
    pitch_to_edge_pitch, generate_voiceover_audio, mix_voiceover_into_video,
    process_voiceover_stage, AVAILABLE_VOICES,
)
from .pipeline import run_pipeline

__all__ = [
    "STYLE_PRESETS", "resolve_style",
    "retry", "has_gpu", "get_device",
    "download_youtube", "get_video_info", "search_youtube",
    "transcribe_video",
    "analyze_faces", "detect_scene_changes", "detect_screen_share",
    "visual_quality", "inspect_render", "media_stream_summary",
    "analyze_content", "batch_analyze_with_ai",
    "render_clip", "concatenate_clips", "mix_bgm", "normalize_audio",
    "get_available_voices", "resolve_voice_id", "speed_to_edge_rate",
    "pitch_to_edge_pitch", "generate_voiceover_audio", "mix_voiceover_into_video",
    "process_voiceover_stage", "AVAILABLE_VOICES",
    "run_pipeline",
]
