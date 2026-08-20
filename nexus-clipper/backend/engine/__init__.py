"""
NexuX V9.5 — Engine Package
============================================
Modular architecture with Opus Killer enhancements:

V8.5 modules (existing):
- constants, styles, utils, download, transcribe, vision, vision_quality
- analyze, render, render_pro, voiceover, pipeline
- virality_score, caption_engine_v2, subtitle_quality
- critic, creative_brain, hook_detection, reframe_engine
- autopost_engine, analytics_engine, repair_system
- preview_renderer, rerender_pipeline

V9.5 NEW modules:
- opus_killer: Unified 8-dimension scoring that beats Opus Clip
- podcast_analyzer: Podcast-specific clip detection (topic segmentation, punchlines, heat)
- clip_titler: Auto-generate viral titles + hashtags + descriptions
- keyword_expander: Expand keyword into related search terms (Mode 2)
- mode_router: Clean mode selection between Podcast and Creative modes
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
from .virality_score import (
    score_clip_virality, score_batch, score_to_api_dict, ViralityScore
)
from .caption_engine_v2 import (
    build_advanced_ass, score_caption_quality, ANIMATIONS, ADVANCED_STYLE_PROPS
)
from .hook_detection import (
    detect_best_hook, detect_hooks_batch, hook_to_api_dict, HookResult
)
from .reframe_engine import (
    auto_reframe, reframe_to_api_dict, ReframeResult, CropInstruction
)
from .autopost_engine import (
    post_to_all_platforms, optimize_metadata_for_platform, validate_video_for_platform,
    list_platforms, results_to_api_dict, PLATFORM_SPECS, PostResult
)
from .analytics_engine import (
    collect_clip_metrics, analyze_clip_performance, analyze_job_performance,
    clip_analytics_to_api_dict, job_analytics_to_api_dict,
    ClipMetrics, ClipAnalytics, JobAnalytics
)
from .repair_system import (
    run_full_diagnosis, fix_issue, fix_all, quick_health_check,
    DiagnosticResult, ALL_CHECKS,
)
from .preview_renderer import (
    generate_preview, generate_preview_frame, PreviewResult,
)
from .rerender_pipeline import (
    rerender_clip_with_personalization, rerender_all_clips, rerender_with_reframe,
    editor_state_to_render_config, build_style_config, build_zoom_filter,
    apply_watermark, apply_audio_processing,
)

# ── V9.5 NEW ──
from .opus_killer import score_with_opus_killer, OpusKillerScore
from .podcast_analyzer import analyze_podcast, detect_filler_words
from .clip_titler import generate_clip_titles, generate_hashtags, generate_description
from .keyword_expander import expand_keyword, get_search_strategy
from .mode_router import get_mode_config, get_all_modes, validate_mode_input, ModeConfig

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
    "score_clip_virality", "score_batch", "score_to_api_dict", "ViralityScore",
    "build_advanced_ass", "score_caption_quality", "ANIMATIONS", "ADVANCED_STYLE_PROPS",
    "detect_best_hook", "detect_hooks_batch", "hook_to_api_dict", "HookResult",
    "auto_reframe", "reframe_to_api_dict", "ReframeResult", "CropInstruction",
    "post_to_all_platforms", "optimize_metadata_for_platform", "validate_video_for_platform",
    "list_platforms", "results_to_api_dict", "PLATFORM_SPECS", "PostResult",
    "collect_clip_metrics", "analyze_clip_performance", "analyze_job_performance",
    "clip_analytics_to_api_dict", "job_analytics_to_api_dict",
    "ClipMetrics", "ClipAnalytics", "JobAnalytics",
    # V9.5
    "score_with_opus_killer", "OpusKillerScore",
    "analyze_podcast", "detect_filler_words",
    "generate_clip_titles", "generate_hashtags", "generate_description",
    "expand_keyword", "get_search_strategy",
    "get_mode_config", "get_all_modes", "validate_mode_input", "ModeConfig",
]
