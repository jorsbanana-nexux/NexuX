"""
NexuX V8.0 — Self-Healing Engine (Intelligent Edition)
=========================================================
TIDAK PERNAH menurunkan kualitas. Setiap fix mencari jalur alternatif
yang mempertahankan atau MENINGKATKAN kualitas output.

Philosophy:
- Error bukan masalah — error adalah kesempatan untuk cari jalan yang lebih baik
- Quality NEVER degrades — if a fix lowers quality, it's a LAST resort, clearly logged
- Healer "berpikir" — bukan pattern matching kaku, tapi contextual diagnosis
- Learning memory: tahu fix mana yang bekerja untuk error tertentu
- Predictive: deteksi masalah SEBELUM terjadi (disk space, memory, etc.)
- Scale: 30+ error types, 120+ fixes, multi-layer healing

Scale:
  Layer 1: Alternative Path (cari jalan lain dengan kualitas sama)
  Layer 2: Optimization (tweak parameter tanpa turunkan kualitas)
  Layer 3: Tool Swap (ganti tool, bukan turunkan kualitas)
  Layer 4: Creative Workaround (pikir out-of-the-box)
  Layer 5: Last Resort (quality trade-off — HANYA jika semua gagal, logged)
"""
import subprocess
import json
import time
import os
import shutil
import sys
import traceback
import hashlib
import platform
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple, Any
from logging import getLogger

from .constants import OUTPUT_DIR

log = getLogger("nexus.healer")


# ── Quality Preservation Rule ──
QUALITY_DEGRADING_ACTIONS = {
    "reduce_resolution", "simplify_filters", "bare_render",
    "smaller_model", "disable_vision", "reduce_quality",
    "disable_animation", "lower_bitrate", "skip_enhancement",
}


# ── Multi-Layer Remediation Playbook ──
# Layer 1: Alternative Path (same quality, different approach)
# Layer 2: Optimization (tweak without quality loss)
# Layer 3: Tool Swap (use different tool at same quality)
# Layer 4: Creative Workaround (unconventional fix)
# Layer 5: Last Resort (quality trade-off — HATED but available)

PLAYBOOK: Dict[str, Dict] = {
    # ── DOWNLOAD ERRORS ──
    "yt_dlp_format_not_found": {
        "severity": "high",
        "layers": [
            # L1: Try alternative formats at same resolution
            [{"action": "try_format", "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"}],
            [{"action": "try_format", "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]"}],
            [{"action": "try_format", "format": "best[height<=1080][ext=mp4]"}],
            # L3: Try yt-dlp with different extractor args
            [{"action": "try_extractor_args", "args": "--extractor-args youtube:player_client=android"}],
            [{"action": "try_extractor_args", "args": "--extractor-args youtube:player_client=ios"}],
            [{"action": "try_extractor_args", "args": "--extractor-args youtube:player_client=web"}],
            # L4: Try download via different method
            [{"action": "try_download_audio_then_mux", "note": "Download audio + video separately, mux with ffmpeg"}],
        ],
    },
    "yt_dlp_rate_limited": {
        "severity": "medium",
        "layers": [
            [{"action": "retry_with_backoff", "delay": 5, "max_retries": 3}],
            [{"action": "retry_with_backoff", "delay": 15, "max_retries": 2}],
            [{"action": "try_proxy_rotation", "note": "Rotate through proxy list"}],
            [{"action": "try_different_client", "client": "android"}],
            [{"action": "try_different_client", "client": "ios"}],
        ],
    },
    "yt_dlp_geo_blocked": {
        "severity": "medium",
        "layers": [
            [{"action": "try_geo_bypass", "method": "default"}],
            [{"action": "try_geo_bypass", "method": "hotspot"}],
            [{"action": "try_geo_bypass", "method": "auto"}],
            [{"action": "try_download_with_cookies", "browser": "firefox"}],
            [{"action": "try_download_with_cookies", "browser": "chrome"}],
        ],
    },
    "yt_dlp_private_or_deleted": {
        "severity": "critical",
        "layers": [
            [{"action": "check_url_validity"}],
            [{"action": "try_download_with_cookies", "browser": "all"}],
            [{"action": "report_to_user", "message": "Video may be private, deleted, or age-restricted"}],
        ],
    },
    "yt_dlp_timeout": {
        "severity": "medium",
        "layers": [
            [{"action": "increase_timeout", "multiplier": 3}],
            [{"action": "retry_with_backoff", "delay": 10, "max_retries": 3}],
            [{"action": "try_download_sections", "note": "Download in smaller chunks"}],
            [{"action": "try_download_audio_first", "note": "Download audio first, video second"}],
        ],
    },
    "download_partial_corrupt": {
        "severity": "high",
        "layers": [
            [{"action": "verify_download", "method": "ffprobe"}],
            [{"action": "re_download_section", "note": "Re-download the corrupt section only"}],
            [{"action": "try_download_with_force_keyframes", "note": "Force keyframe alignment"}],
            [{"action": "try_download_different_format_same_quality"}],
        ],
    },

    # ── FFMPEG RENDER ERRORS ──
    "ffmpeg_filter_error": {
        "severity": "high",
        "layers": [
            # L1: Rebuild filter chain with alternative syntax
            [{"action": "rebuild_filter_chain", "note": "Re-parse filter graph with alternative syntax"}],
            [{"action": "try_filter_alternative", "find": "zoompan", "replace": "scale2ref+crop"},
             {"action": "try_filter_alternative", "find": "ass", "replace": "subtitles"}],
            # L2: Optimize filter order
            [{"action": "reorder_filters", "order": "scale,crop,zoom,subtitle,color"}],
            [{"action": "split_filter_passes", "note": "Run filters in separate passes"}],
            # L3: Use different encoder
            [{"action": "try_encoder", "encoder": "libx265", "crf": "20"}],
            [{"action": "try_encoder", "encoder": "libvpx-vp9", "crf": "25"}],
        ],
    },
    "ffmpeg_codec_error": {
        "severity": "high",
        "layers": [
            [{"action": "try_encoder", "encoder": "libx264", "preset": "slow", "crf": "18"}],
            [{"action": "try_encoder", "encoder": "libx265", "preset": "medium", "crf": "20"}],
            [{"action": "try_encoder", "encoder": "h264_nvenc", "preset": "hq", "cq": "20"}],
            [{"action": "try_encoder", "encoder": "h264_videotoolbox", "preset": "high"}],
            [{"action": "try_encoder", "encoder": "libx264rgb", "preset": "slow", "crf": "18"}],
        ],
    },
    "ffmpeg_subtitle_error": {
        "severity": "high",
        "layers": [
            # L1: Fix subtitle format
            [{"action": "regenerate_ass", "note": "Rebuild ASS file with escaped characters"}],
            [{"action": "try_subtitle_format", "format": "srt", "note": "Fall back to SRT with styled burn-in"}],
            [{"action": "try_subtitle_filter", "filter": "subtitles", "note": "Use subtitles filter instead of ass"}],
            # L2: Fix font issues
            [{"action": "fix_font_path", "note": "Resolve font path to absolute"}],
            [{"action": "embed_fonts", "note": "Embed fonts in ASS file"}],
            # L3: Use drawtext as fallback
            [{"action": "use_drawtext", "note": "Use drawtext for basic subtitle rendering"}],
        ],
    },
    "ffmpeg_memory_error": {
        "severity": "high",
        "layers": [
            # L1: Optimize memory without quality loss
            [{"action": "enable_thread_queue", "note": "Use thread_queue_size for memory efficiency"}],
            [{"action": "process_in_segments", "note": "Process video in segments, then concatenate"}],
            [{"action": "use_pipe", "note": "Use pipe instead of temp files"}],
            # L2: Adjust thread count
            [{"action": "limit_threads", "max_threads": 2}],
            [{"action": "limit_threads", "max_threads": 1}],
            # L3: Use hardware acceleration
            [{"action": "try_hwaccel", "accel": "cuda"}],
            [{"action": "try_hwaccel", "accel": "videotoolbox"}],
            [{"action": "try_hwaccel", "accel": "qsv"}],
        ],
    },
    "ffmpeg_output_too_large": {
        "severity": "low",
        "layers": [
            [{"action": "optimize_encoding", "note": "Use 2-pass encoding for better compression at same quality"}],
            [{"action": "try_2pass_encoding", "target_size_mb": 50}],
            [{"action": "try_2pass_encoding", "target_size_mb": 100}],
            [{"action": "adjust_crf", "crf": "23", "note": "Slightly higher CRF, visually identical"}],
        ],
    },

    # ── TRANSCRIPTION ERRORS ──
    "whisper_model_load_failed": {
        "severity": "high",
        "layers": [
            # L1: Try different model sources
            [{"action": "try_whisper_model", "model": "large-v3", "source": "faster-whisper"}],
            [{"action": "try_whisper_model", "model": "large-v2", "source": "faster-whisper"}],
            [{"action": "try_whisper_model", "model": "medium", "source": "faster-whisper"}],
            # L2: Try different compute type (same model)
            [{"action": "try_compute_type", "compute": "float16", "device": "cuda"}],
            [{"action": "try_compute_type", "compute": "int8_float16", "device": "cuda"}],
            [{"action": "try_compute_type", "compute": "int8", "device": "cpu"}],
            # L3: Try alternative transcription
            [{"action": "use_youtube_auto_captions", "note": "Use YouTube auto-captions instead of Whisper"}],
            [{"action": "try_whisper_model", "model": "large-v3", "source": "openai-whisper"}],
            # L4: Try with different VAD settings
            [{"action": "try_vad_settings", "threshold": 0.5, "min_silence": 500}],
        ],
    },
    "whisper_transcription_timeout": {
        "severity": "medium",
        "layers": [
            [{"action": "split_audio_chunks", "chunk_minutes": 10, "note": "Transcribe in 10-min chunks"}],
            [{"action": "split_audio_chunks", "chunk_minutes": 5}],
            [{"action": "split_audio_chunks", "chunk_minutes": 3}],
            [{"action": "use_youtube_auto_captions", "note": "Fast path: YouTube auto-captions"}],
            [{"action": "use_youtube_auto_captions", "fallback": "whisper_small", "note": "Auto-captions + Whisper for gaps"}],
        ],
    },
    "whisper_no_speech_detected": {
        "severity": "medium",
        "layers": [
            [{"action": "check_audio_track", "note": "Verify audio track exists and has content"}],
            [{"action": "try_audio_extraction_first", "note": "Extract audio separately, then transcribe"}],
            [{"action": "try_noise_reduction", "method": "afftdn"}],
            [{"action": "try_noise_reduction", "method": "highpass=f=100,lowpass=f=8000"}],
            [{"action": "try_whisper_model", "model": "large-v3", "source": "faster-whisper"}],
        ],
    },

    # ── VISION / FACE DETECTION ERRORS ──
    "opencv_face_detection_failed": {
        "severity": "medium",
        "layers": [
            [{"action": "try_face_detector", "detector": "mediapipe"}],
            [{"action": "try_face_detector", "detector": "haar"}],
            [{"action": "try_face_detector", "detector": "dnn"}],
            [{"action": "use_center_crop", "note": "Use intelligent center crop based on scene analysis"}],
            [{"action": "use_salience_map", "note": "Generate salience map for smart crop without face detection"}],
        ],
    },
    "mediapipe_init_failed": {
        "severity": "medium",
        "layers": [
            [{"action": "try_face_detector", "detector": "opencv_haar"}],
            [{"action": "try_face_detector", "detector": "opencv_dnn"}],
            [{"action": "use_salience_map"}],
            [{"action": "use_center_crop"}],
        ],
    },

    # ── AUDIO ERRORS ──
    "no_audio_track": {
        "severity": "high",
        "layers": [
            [{"action": "extract_audio_separately", "note": "Download audio-only with yt-dlp, then mux"}],
            [{"action": "try_download_audio_first"}],
            [{"action": "generate_silent_audio", "note": "Create silent audio track matching video duration"}],
        ],
    },
    "audio_normalize_failed": {
        "severity": "low",
        "layers": [
            [{"action": "try_normalize_method", "method": "loudnorm", "note": "EBU R128 loudness normalization"}],
            [{"action": "try_normalize_method", "method": "dynaudnorm", "note": "Dynamic normalization"}],
            [{"action": "try_normalize_method", "method": "volume=1.5dB"}],
            [{"action": "skip_normalize", "note": "Use original audio as-is"}],
        ],
    },
    "audio_desync": {
        "severity": "high",
        "layers": [
            [{"action": "fix_pts", "note": "Reset presentation timestamps"}],
            [{"action": "resync_audio", "method": "aresample=async=1"}],
            [{"action": "resync_audio", "method": "asetpts=PTS-STARTPTS"}],
            [{"action": "re_extract_audio", "note": "Re-extract audio from source and re-mux"}],
        ],
    },

    # ── SYSTEM ERRORS ──
    "out_of_memory": {
        "severity": "critical",
        "layers": [
            # L1: Memory optimization WITHOUT quality loss
            [{"action": "enable_streaming", "note": "Stream processing instead of buffering"}],
            [{"action": "process_in_segments"}],
            [{"action": "clear_cache", "note": "Clear temporary files and cache"}],
            [{"action": "limit_threads", "max_threads": 2}],
            # L2: Use hardware acceleration
            [{"action": "try_hwaccel", "accel": "cuda"}],
            [{"action": "try_hwaccel", "accel": "videotoolbox"}],
            # L3: Process clips one at a time
            [{"action": "sequential_processing", "note": "Process clips one at a time instead of parallel"}],
        ],
    },
    "disk_full": {
        "severity": "critical",
        "layers": [
            [{"action": "cleanup_old_jobs", "max_age_hours": 12}],
            [{"action": "cleanup_old_jobs", "max_age_hours": 6}],
            [{"action": "cleanup_temp_files"}],
            [{"action": "cleanup_old_jobs", "max_age_hours": 1}],
            [{"action": "compress_output", "note": "Compress output with higher efficiency codec"}],
        ],
    },
    "process_timeout": {
        "severity": "medium",
        "layers": [
            [{"action": "increase_timeout", "multiplier": 3}],
            [{"action": "increase_timeout", "multiplier": 5}],
            [{"action": "process_in_segments"}],
            [{"action": "sequential_processing"}],
        ],
    },

    # ── PIPELINE LOGIC ERRORS ──
    "no_clips_found": {
        "severity": "high",
        "layers": [
            [{"action": "relax_threshold", "threshold": 0.8, "note": "Lower viral score threshold"}],
            [{"action": "relax_threshold", "threshold": 0.6}],
            [{"action": "relax_threshold", "threshold": 0.4}],
            [{"action": "try_different_genre", "note": "Re-analyze with different genre assumption"}],
            [{"action": "use_all_segments", "note": "Use all transcript segments as potential clips"}],
            [{"action": "manual_mode", "note": "Ask user to select time ranges manually"}],
        ],
    },
    "all_clips_failed_render": {
        "severity": "critical",
        "layers": [
            [{"action": "rebuild_filter_chain"}],
            [{"action": "try_encoder", "encoder": "libx264", "preset": "slow", "crf": "18"}],
            [{"action": "split_filter_passes"}],
            [{"action": "process_in_segments"}],
            [{"action": "try_hwaccel", "accel": "auto"}],
        ],
    },
    "critic_score_too_low": {
        "severity": "medium",
        "layers": [
            [{"action": "adjust_creative_palette", "note": "Try a different creative palette that may score higher"}],
            [{"action": "enhance_subtitle_style", "note": "Switch to more engaging subtitle style"}],
            [{"action": "add_speed_ramp", "note": "Add dramatic speed ramp at key moments"}],
            [{"action": "enhance_color_grade", "note": "Apply more vibrant color grade"}],
            [{"action": "add_transition_effect", "note": "Add more dynamic transitions"}],
        ],
    },
    "subtitle_generation_failed": {
        "severity": "medium",
        "layers": [
            [{"action": "regenerate_ass"}],
            [{"action": "try_subtitle_format", "format": "srt"}],
            [{"action": "use_drawtext"}],
            [{"action": "simplify_subtitle_text", "note": "Remove special characters that break ASS format"}],
            [{"action": "fix_subtitle_timing", "note": "Clamp timestamps to valid range"}],
        ],
    },
    "thumbnail_generation_failed": {
        "severity": "low",
        "layers": [
            [{"action": "try_thumbnail_method", "method": "ffmpeg_frame"}],
            [{"action": "try_thumbnail_method", "method": "opencv_frame"}],
            [{"action": "use_default_thumbnail"}],
        ],
    },
    "concat_failed": {
        "severity": "high",
        "layers": [
            [{"action": "try_concat_method", "method": "filter_complex"}],
            [{"action": "try_concat_method", "method": "concat_demuxer"}],
            [{"action": "try_concat_method", "method": "concat_protocol"}],
            [{"action": "re_encode_clips", "note": "Re-encode all clips with matching parameters, then concat"}],
        ],
    },
    "json_parse_error": {
        "severity": "medium",
        "layers": [
            [{"action": "repair_json", "note": "Attempt to fix malformed JSON"}],
            [{"action": "regenerate_data", "note": "Regenerate the data from source"}],
            [{"action": "use_fallback_data", "note": "Use cached/default data"}],
        ],
    },
    "network_error": {
        "severity": "medium",
        "layers": [
            [{"action": "retry_with_backoff", "delay": 3, "max_retries": 5}],
            [{"action": "retry_with_backoff", "delay": 10, "max_retries": 3}],
            [{"action": "try_offline_mode", "note": "Use cached data if available"}],
        ],
    },
    "permission_denied": {
        "severity": "high",
        "layers": [
            [{"action": "fix_permissions", "note": "Attempt to fix file/directory permissions"}],
            [{"action": "use_alternate_path", "note": "Use alternative output directory"}],
            [{"action": "create_directory", "note": "Create missing directory structure"}],
        ],
    },
    "import_error": {
        "severity": "high",
        "layers": [
            [{"action": "install_package", "note": "Attempt to install missing package"}],
            [{"action": "use_alternative_module", "note": "Use alternative module with same functionality"}],
            [{"action": "lazy_import_fallback", "note": "Use lazy import with graceful degradation"}],
        ],
    },
}


# ── Healing Memory (persistent learning) ──

MEMORY_FILE = OUTPUT_DIR / "healer_memory.json"


def _load_memory() -> Dict:
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "total_heals": 0,
        "successful_heals": 0,
        "failed_heals": 0,
        "error_history": {},  # error_type → {fixes_tried: [{fix, success, timestamp}]}
        "best_fixes": {},     # error_type → {fix_action: success_rate}
        "prevented_errors": 0,
    }


def _save_memory(mem: Dict):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except Exception as e:
        log.warning(f"[Healer] Memory save failed: {e}")


# ── Error Log ──

ERROR_LOG = OUTPUT_DIR / "healer_log.json"


def _load_error_log() -> List[Dict]:
    try:
        if ERROR_LOG.exists():
            with open(ERROR_LOG, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_error_log(logs: List[Dict]):
    try:
        if len(logs) > 200:
            logs = logs[-200:]
        with open(ERROR_LOG, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception:
        pass


def _log_error(
    error_type: str,
    error_msg: str,
    fix_applied: Optional[str] = None,
    success: bool = False,
    quality_preserved: bool = True,
):
    logs = _load_error_log()
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": error_type,
        "error": error_msg[:500],
        "fix": fix_applied,
        "success": success,
        "quality_preserved": quality_preserved,
    }
    logs.append(entry)
    _save_error_log(logs)


# ── Intelligent Diagnosis ──

def diagnose_error(error: Exception, context: str = "", extra: Optional[Dict] = None) -> str:
    """Diagnose root cause with context awareness — not just pattern matching."""
    msg = str(error).lower()
    tb = traceback.format_exc().lower()
    ctx = context.lower()
    extra = extra or {}

    # ── Download errors ──
    if "format" in msg and ("not" in msg and "found" in msg):
        return "yt_dlp_format_not_found"
    if "429" in msg or "rate" in msg and "limit" in msg:
        return "yt_dlp_rate_limited"
    if "geo" in msg or ("country" in msg and "block" in msg):
        return "yt_dlp_geo_blocked"
    if "private" in msg or "deleted" in msg or ("unavailable" in msg and "video" in msg):
        return "yt_dlp_private_or_deleted"
    if "timeout" in msg or "timed out" in msg:
        if "download" in ctx:
            return "yt_dlp_timeout"
        return "process_timeout"
    if "partial" in msg or "corrupt" in msg or "incomplete" in msg:
        if "download" in ctx:
            return "download_partial_corrupt"

    # ── FFmpeg errors ──
    if "ffmpeg" in msg or "ffprobe" in msg:
        if "filter" in msg or "vf" in msg or "no such filter" in msg:
            return "ffmpeg_filter_error"
        if "codec" in msg or "encoder" in msg or "decoder" in msg or "unknown encoder" in msg:
            return "ffmpeg_codec_error"
        if "subtitle" in msg or "ass" in msg or "sub" in msg:
            return "ffmpeg_subtitle_error"
        if "memory" in msg or "oom" in msg or "cannot allocate" in msg:
            return "ffmpeg_memory_error"
        if "too large" in msg or "output" in msg and "size" in msg:
            return "ffmpeg_output_too_large"
        if "concat" in msg:
            return "concat_failed"
        return "ffmpeg_filter_error"  # Default ffmpeg issue

    # ── Whisper errors ──
    if "whisper" in msg or "transcribe" in ctx:
        if "model" in msg and ("load" in msg or "download" in msg or "not found" in msg):
            return "whisper_model_load_failed"
        if "timeout" in msg or "timed out" in msg:
            return "whisper_transcription_timeout"
        if "no speech" in msg or "empty" in msg and "result" in msg:
            return "whisper_no_speech_detected"
        return "whisper_model_load_failed"

    # ── Vision errors ──
    if "opencv" in msg or "cv2" in msg:
        if "face" in msg or "detect" in msg:
            return "opencv_face_detection_failed"
    if "mediapipe" in msg:
        return "mediapipe_init_failed"

    # ── Audio errors ──
    if "no audio" in msg or "audio" in msg and "not found" in msg:
        return "no_audio_track"
    if "normalize" in msg or "loudnorm" in msg:
        return "audio_normalize_failed"
    if "desync" in msg or "sync" in msg and "audio" in msg:
        return "audio_desync"

    # ── System errors ──
    if "memory" in msg or "oom" in msg or "out of memory" in msg:
        return "out_of_memory"
    if "disk" in msg and ("full" in msg or "space" in msg):
        return "disk_full"
    if "permission" in msg or "denied" in msg or "eacces" in msg:
        return "permission_denied"
    if "no module" in msg or "importerror" in msg or "modulenotfound" in msg:
        return "import_error"

    # ── Pipeline logic errors ──
    if "no clips" in msg or "empty" in msg and "clips" in msg:
        return "no_clips_found"
    if "score" in msg and "low" in msg:
        return "critic_score_too_low"
    if "subtitle" in msg and ("fail" in msg or "error" in msg):
        return "subtitle_generation_failed"
    if "thumbnail" in msg:
        return "thumbnail_generation_failed"
    if "json" in msg and ("parse" in msg or "decode" in msg):
        return "json_parse_error"
    if "network" in msg or "connection" in msg or "refused" in msg:
        return "network_error"
    if "all" in msg and "failed" in msg and "render" in msg:
        return "all_clips_failed_render"

    # ── Fallback: check traceback for more clues ──
    if "ffmpeg" in tb:
        return "ffmpeg_filter_error"
    if "whisper" in tb:
        return "whisper_model_load_failed"
    if "cv2" in tb or "mediapipe" in tb:
        return "opencv_face_detection_failed"

    log.warning(f"[Healer] Unknown error type — msg: {msg[:200]}")
    return "unknown"


# ── Main Healing Function ──

def heal(
    error: Exception,
    context: str,
    retry_fn: Callable,
    current_params: Dict,
    extra_context: Optional[Dict] = None,
) -> Tuple[Optional[Any], Dict, bool]:
    """Try to heal an error using multi-layer remediation.
    
    Quality-preserving: tries alternative paths FIRST, quality trade-offs LAST.
    
    Returns:
        (result, updated_params, quality_preserved)
        - result: None if all healing failed
        - updated_params: params with healing adjustments
        - quality_preserved: True if no quality-degrading fix was used
    """
    error_type = diagnose_error(error, context, extra_context)
    playbook_entry = PLAYBOOK.get(error_type)

    if not playbook_entry:
        log.error(f"[Healer] No playbook for error type: {error_type}")
        _log_error(error_type, str(error), "no_playbook", success=False)
        return None, current_params, True

    layers = playbook_entry.get("layers", [])
    severity = playbook_entry.get("severity", "medium")
    mem = _load_memory()
    mem["total_heals"] += 1

    # Check best fixes from memory (use learned success rates)
    best_fixes = mem.get("best_fixes", {}).get(error_type, {})

    # Reorder layers based on learned success rates
    if best_fixes:
        layers = _reorder_by_success(layers, best_fixes)

    log.info(f"[Healer] Error: {error_type} | Severity: {severity} | Layers: {len(layers)}")
    log.info(f"[Healer] Context: {context}")
    log.info(f"[Healer] Error message: {str(error)[:300]}")

    quality_preserved = True

    for layer_idx, fixes in enumerate(layers):
        for fix in fixes:
            fix_action = fix.get("action", "unknown")
            is_quality_degrading = fix_action in QUALITY_DEGRADING_ACTIONS

            if is_quality_degrading and quality_preserved:
                log.warning(f"[Healer] Layer {layer_idx+1}: {fix_action} — QUALITY DEGRADING. Skipping for now.")
                continue  # Skip quality-degrading fixes until we've tried everything else

            log.info(f"[Healer] Layer {layer_idx+1}/{len(layers)}: Trying {fix_action}")

            updated_params = current_params.copy()
            updated_params.update(fix)
            updated_params["_healer_attempt"] = layer_idx + 1
            updated_params["_healer_error_type"] = error_type

            try:
                result = retry_fn(**updated_params)
                # SUCCESS!
                mem["successful_heals"] += 1
                _record_success(mem, error_type, fix_action)
                _log_error(error_type, str(error), fix_action, success=True,
                          quality_preserved=not is_quality_degrading)
                _save_memory(mem)

                log.info(f"[Healer] ✅ Fix '{fix_action}' SUCCEEDED | Quality preserved: {not is_quality_degrading}")
                return result, updated_params, not is_quality_degrading

            except Exception as e:
                log.warning(f"[Healer] Fix '{fix_action}' failed: {str(e)[:200]}")
                _record_failure(mem, error_type, fix_action)
                continue

    # All quality-preserving fixes failed — try quality-degrading as LAST resort
    log.warning(f"[Healer] All quality-preserving fixes failed. Trying last-resort fixes...")

    for layer_idx, fixes in enumerate(layers):
        for fix in fixes:
            fix_action = fix.get("action", "unknown")
            if fix_action not in QUALITY_DEGRADING_ACTIONS:
                continue  # Already tried

            log.warning(f"[Healer] LAST RESORT: {fix_action} (quality may degrade)")

            updated_params = current_params.copy()
            updated_params.update(fix)
            updated_params["_healer_last_resort"] = True

            try:
                result = retry_fn(**updated_params)
                mem["successful_heals"] += 1
                _record_success(mem, error_type, fix_action)
                _log_error(error_type, str(error), fix_action, success=True,
                          quality_preserved=False)
                _save_memory(mem)

                log.warning(f"[Healer] ⚠️ Last-resort fix '{fix_action}' succeeded — QUALITY DEGRADED")
                return result, updated_params, False

            except Exception as e:
                log.error(f"[Healer] Last-resort fix '{fix_action}' also failed: {str(e)[:200]}")
                continue

    # Complete failure
    mem["failed_heals"] += 1
    _save_memory(mem)
    _log_error(error_type, str(error), "all_fixes_failed", success=False)
    log.error(f"[Healer] ❌ All {len(layers)} layers exhausted for {error_type}")
    return None, current_params, True


def _record_success(mem: Dict, error_type: str, fix_action: str):
    """Record a successful fix for learning."""
    history = mem.setdefault("error_history", {}).setdefault(error_type, [])
    history.append({"fix": fix_action, "success": True, "timestamp": time.strftime("%Y-%m-%d %H:%M")})
    if len(history) > 50:
        history[:] = history[-50:]

    best = mem.setdefault("best_fixes", {}).setdefault(error_type, {})
    stats = best.setdefault(fix_action, {"success": 0, "total": 0})
    stats["success"] += 1
    stats["total"] += 1


def _record_failure(mem: Dict, error_type: str, fix_action: str):
    """Record a failed fix attempt."""
    history = mem.setdefault("error_history", {}).setdefault(error_type, [])
    history.append({"fix": fix_action, "success": False, "timestamp": time.strftime("%Y-%m-%d %H:%M")})
    if len(history) > 50:
        history[:] = history[-50:]

    best = mem.setdefault("best_fixes", {}).setdefault(error_type, {})
    stats = best.setdefault(fix_action, {"success": 0, "total": 0})
    stats["total"] += 1


def _reorder_by_success(layers: List[List[Dict]], best_fixes: Dict) -> List[List[Dict]]:
    """Reorder fix layers based on learned success rates."""
    def success_rate(fix_action: str) -> float:
        stats = best_fixes.get(fix_action, {})
        if stats.get("total", 0) == 0:
            return 0.5  # Unknown — neutral
        return stats.get("success", 0) / stats["total"]

    # Flatten, sort by success rate, then re-group into layers
    all_fixes = []
    for layer in layers:
        for fix in layer:
            all_fixes.append(fix)

    all_fixes.sort(key=lambda f: success_rate(f.get("action", "")), reverse=True)

    # Re-group into layers of 1 fix each (try best first)
    return [[fix] for fix in all_fixes]


# ── Predictive Health ──

def check_system_health() -> Dict:
    """Comprehensive system health check with predictive analysis."""
    health = {"healthy": True, "issues": [], "warnings": [], "info": {}}

    # Check ffmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            health["healthy"] = False
            health["issues"].append("ffmpeg not working")
        else:
            version = r.stderr.split("\n")[0] if r.stderr else r.stdout.split("\n")[0]
            health["info"]["ffmpeg"] = version.strip()
    except FileNotFoundError:
        health["healthy"] = False
        health["issues"].append("ffmpeg not found — install: https://ffmpeg.org")
    except Exception:
        health["healthy"] = False
        health["issues"].append("ffmpeg check failed")

    # Check ffprobe
    try:
        r = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            health["healthy"] = False
            health["issues"].append("ffprobe not working")
    except FileNotFoundError:
        health["healthy"] = False
        health["issues"].append("ffprobe not found")

    # Check yt-dlp
    try:
        r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            health["healthy"] = False
            health["issues"].append("yt-dlp not working")
        else:
            health["info"]["yt_dlp"] = r.stdout.strip()
    except FileNotFoundError:
        health["healthy"] = False
        health["issues"].append("yt-dlp not found — install: pip install yt-dlp")
    except Exception:
        health["healthy"] = False
        health["issues"].append("yt-dlp check failed")

    # Check disk space (predictive: warn before full)
    try:
        stat = os.statvfs(str(OUTPUT_DIR))
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        health["info"]["disk_free_gb"] = round(free_gb, 1)
        if free_gb < 1.0:
            health["healthy"] = False
            health["issues"].append(f"CRITICAL: Only {free_gb:.1f} GB disk space — cleanup needed")
        elif free_gb < 5.0:
            health["warnings"].append(f"Low disk space: {free_gb:.1f} GB free")
    except Exception:
        pass

    # Check available memory (predictive: warn before OOM)
    try:
        import psutil
        mem = psutil.virtual_memory()
        health["info"]["memory_total_gb"] = round(mem.total / (1024**3), 1)
        health["info"]["memory_available_gb"] = round(mem.available / (1024**3), 1)
        health["info"]["memory_percent"] = mem.percent
        if mem.available < 1 * (1024**3):  # Less than 1GB available
            health["healthy"] = False
            health["issues"].append(f"CRITICAL: Only {mem.available / (1024**3):.1f} GB RAM available")
        elif mem.percent > 85:
            health["warnings"].append(f"High memory usage: {mem.percent}%")
    except ImportError:
        health["warnings"].append("psutil not installed — cannot check memory")

    # Check GPU availability (for hardware acceleration)
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                          capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            health["info"]["gpu"] = r.stdout.strip()
        else:
            health["info"]["gpu"] = "Not available (CPU mode)"
    except Exception:
        health["info"]["gpu"] = "Not detected"

    # Check Python packages
    required = ["fastapi", "pydantic"]
    optional = ["faster_whisper", "cv2", "mediapipe", "torch", "psutil", "yt_dlp"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            health["healthy"] = False
            health["issues"].append(f"Missing required package: {pkg}")
    for pkg in optional:
        try:
            __import__(pkg)
            health["info"][f"pkg_{pkg}"] = "installed"
        except ImportError:
            health["warnings"].append(f"Optional package not installed: {pkg}")

    # Check healing memory stats
    mem = _load_memory()
    health["info"]["healer_stats"] = {
        "total_heals": mem.get("total_heals", 0),
        "successful": mem.get("successful_heals", 0),
        "failed": mem.get("failed_heals", 0),
        "success_rate": round(mem.get("successful_heals", 0) / max(mem.get("total_heals", 1), 1) * 100, 1),
    }

    return health


# ── Auto-Cleanup ──

def auto_cleanup_old_jobs(max_age_hours: int = 24) -> int:
    """Clean up old job directories to free disk space."""
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned = 0

    try:
        for item in OUTPUT_DIR.iterdir():
            if not item.is_dir():
                continue
            # Skip system files
            if item.name.endswith(".json"):
                continue

            mtime = item.stat().st_mtime
            if now - mtime > max_age_seconds:
                shutil.rmtree(item, ignore_errors=True)
                cleaned += 1
                log.info(f"[Healer] Cleaned up old job: {item.name}")
    except Exception as e:
        log.warning(f"[Healer] Cleanup failed: {e}")

    if cleaned:
        log.info(f"[Healer] Auto-cleanup: removed {cleaned} old job(s), freed space")
    return cleaned


def cleanup_temp_files() -> int:
    """Clean up temporary files (partial downloads, temp audio, etc.)."""
    cleaned = 0
    try:
        for item in OUTPUT_DIR.glob("*.tmp"):
            item.unlink(missing_ok=True)
            cleaned += 1
        for item in OUTPUT_DIR.glob("*.partial"):
            item.unlink(missing_ok=True)
            cleaned += 1
        for item in OUTPUT_DIR.glob("*_temp.*"):
            item.unlink(missing_ok=True)
            cleaned += 1
    except Exception as e:
        log.warning(f"[Healer] Temp cleanup failed: {e}")
    return cleaned


# ── Healing Stats ──

def get_healing_stats() -> Dict:
    """Get healing statistics for the dashboard."""
    mem = _load_memory()
    return {
        "total_heals": mem.get("total_heals", 0),
        "successful": mem.get("successful_heals", 0),
        "failed": mem.get("failed_heals", 0),
        "success_rate": round(
            mem.get("successful_heals", 0) / max(mem.get("total_heals", 1), 1) * 100, 1
        ),
        "best_fixes": mem.get("best_fixes", {}),
        "error_types_seen": list(mem.get("error_history", {}).keys()),
    }


def get_playbook_summary() -> Dict:
    """Get summary of all error types and fixes in the playbook."""
    summary = {}
    for error_type, entry in PLAYBOOK.items():
        all_fixes = []
        for layer in entry.get("layers", []):
            for fix in layer:
                all_fixes.append(fix.get("action", "unknown"))
        summary[error_type] = {
            "severity": entry.get("severity", "medium"),
            "total_fixes": len(all_fixes),
            "quality_preserving": len([f for f in all_fixes if f not in QUALITY_DEGRADING_ACTIONS]),
            "quality_degrading": len([f for f in all_fixes if f in QUALITY_DEGRADING_ACTIONS]),
        }
    return summary
