"""
NexuX V8.5 — Engine Package
============================================
Modular architecture:
- constants.py: All configurations & presets
- styles.py: 30+ subtitle style system
- utils.py: Path/FFmpeg/retry helpers
- download.py: yt-dlp video download
- transcribe.py: WhisperX/Whisper transcription
- vision.py: Face detection, scene analysis, screen detection
- vision_quality.py: Render QA & visual quality assessment
- analyze.py: Viral scoring with AI semantic analysis
- render.py: FFmpeg rendering with ASS subtitles
- render_pro.py: Professional multi-pass render engine
- voiceover.py: Edge-TTS synthesis & audio mixing
- pipeline.py: End-to-end orchestration
- virality_score.py: 8-dimensional virality scoring (0-100)
- caption_engine_v2.py: Advanced kinetic typography captions
- subtitle_quality.py: CPS/readability validation
- critic.py: Editorial critic & revision loop
- creative_brain.py: Creative palette selection & memory
- hook_detection.py: Intelligent hook detection & clip start optimization
- reframe_engine.py: Face-tracking auto-reframe for vertical video
- autopost_engine.py: Multi-platform auto-posting (TikTok, YT, IG, FB, X, LinkedIn)
- analytics_engine.py: Cross-platform analytics & performance prediction
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
]
