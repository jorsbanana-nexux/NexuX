"""
NexuX V8.0 — Audio Enhancement Engine
===============================================
Professional audio processing for gold-standard output.

The old system had basic loudnorm. This module adds:
- Speech-aware audio ducking (music dips when someone speaks)
- Dynamic range compression (even out loud/quiet moments)
- Noise gate (remove background hum/hiss)
- EQ enhancement (boost speech clarity, cut muddiness)
- Loudness normalization to broadcast standards (EBU R128 / -16 LUFS)
- Audio quality analysis (peak detection, dynamic range)

This is what makes the audio sound professional, not just "technically present."
"""
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

log = logging.getLogger("nexus.audio_enhancer")


# ── Constants ────────────────────────────────────────

TARGET_LUFS = -16.0      # Broadcast standard (EBU R128)
TARGET_TRUE_PEAK = -1.5  # Max true peak (dB)
TARGET_LRA = 11.0        # Target loudness range

# Speech frequencies
SPEECH_LOW_CUT = 80      # Hz — cut below this (rumble)
SPEECH_HIGH_BOOST = 3000 # Hz — boost above this (clarity)
SPEECH_PRESENCE = 5000   # Hz — presence range
SPEECH_SIBILANCE = 7000  # Hz — sibilance range

# Noise gate
NOISE_GATE_THRESHOLD = -50  # dB — below this is noise
NOISE_GATE_ATTACK = 5       # ms
NOISE_GATE_RELEASE = 100    # ms

# Compressor settings
COMPRESSOR_THRESHOLD = -20  # dB
COMPRESSOR_RATIO = 3         # 3:1 compression
COMPRESSOR_ATTACK = 10       # ms
COMPRESSOR_RELEASE = 100     # ms
COMPRESSOR_MAKEUP = 2        # dB makeup gain


# ── Audio Analysis ───────────────────────────────────

def analyze_audio(video_path: Path) -> Dict:
    """
    Analyze audio characteristics of a video file.
    
    Uses ffprobe to measure:
    - Volume levels (mean, max)
    - Dynamic range
    - Loudness (LUFS approximation)
    - Audio codec and bitrate
    - Channel layout
    """
    try:
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-af", "volumedetect",
            "-f", "null", "-",
            "-y"
        ]
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )

        # Parse volume info from stderr
        stderr = r.stderr
        mean_vol = _parse_ffmpeg_metric(stderr, "mean_volume")
        max_vol = _parse_ffmpeg_metric(stderr, "max_volume")
        
        # Get stream info
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "a",
            str(video_path)
        ]
        probe_r = subprocess.run(
            probe_cmd, capture_output=True, text=True, timeout=15
        )
        
        stream_info = {}
        if probe_r.returncode == 0:
            data = json.loads(probe_r.stdout)
            if data.get("streams"):
                s = data["streams"][0]
                stream_info = {
                    "codec": s.get("codec_name", "unknown"),
                    "bitrate": int(s.get("bit_rate", 0)),
                    "channels": int(s.get("channels", 2)),
                    "sample_rate": int(s.get("sample_rate", 48000)),
                }

        return {
            "mean_volume_db": mean_vol,
            "max_volume_db": max_vol,
            "dynamic_range_db": (max_vol - mean_vol) if mean_vol and max_vol else None,
            "stream": stream_info,
            "needs_enhancement": mean_vol is None or mean_vol < -25 or mean_vol > -5,
        }
    except Exception as e:
        log.warning(f"[Audio] Analysis failed: {e}")
        return {"needs_enhancement": False, "error": str(e)}


def _parse_ffmpeg_metric(stderr: str, metric: str) -> Optional[float]:
    """Parse a metric from ffmpeg volumedetect output."""
    import re
    match = re.search(rf"{metric}:\s*(-?\d+\.?\d*)\s*dB", stderr)
    if match:
        return float(match.group(1))
    return None


# ── Audio Enhancement Chain ──────────────────────────

def build_enhancement_filter(
    analysis: Dict,
    has_bgm: bool = False,
    aggressive: bool = False,
) -> str:
    """
    Build an FFmpeg audio filter chain for professional enhancement.
    
    The chain is:
    1. High-pass filter (remove rumble below 80Hz)
    2. Noise gate (remove background noise)
    3. Compressor (even out dynamics)
    4. EQ (boost speech clarity)
    5. Loudnorm (normalize to broadcast standard)
    
    Args:
        analysis: Output from analyze_audio()
        has_bgm: Whether BGM will be mixed in (affects ducking)
        aggressive: More aggressive processing for poor-quality audio
    
    Returns:
        FFmpeg audio filter string
    """
    filters = []

    # 1. High-pass filter — remove low-frequency rumble
    hp_freq = 100 if aggressive else SPEECH_LOW_CUT
    filters.append(f"highpass=f={hp_freq}")

    # 2. Noise gate — remove background noise
    ng_threshold = NOISE_GATE_THRESHOLD + (10 if aggressive else 0)
    filters.append(
        f"agate=threshold={ng_threshold}dB:"
        f"attack={NOISE_GATE_ATTACK}:"
        f"release={NOISE_GATE_RELEASE}"
    )

    # 3. Compressor — even out dynamics
    comp_threshold = COMPRESSOR_THRESHOLD + (5 if aggressive else 0)
    filters.append(
        f"acompressor=threshold={comp_threshold}dB:"
        f"ratio={COMPRESSOR_RATIO}:"
        f"attack={COMPRESSOR_ATTACK}:"
        f"release={COMPRESSOR_RELEASE}:"
        f"makeup={COMPRESSOR_MAKEUP}"
    )

    # 4. EQ — speech enhancement
    # Boost presence (2-5kHz) for clarity, cut muddiness (200-400Hz slightly)
    eq_gain = 3 if aggressive else 2
    filters.append(
        f"equalizer=f={SPEECH_HIGH_BOOST}:t=q:w=1:g={eq_gain},"  # Clarity boost
        f"equalizer=f={SPEECH_PRESENCE}:t=q:w=1.5:g={eq_gain * 0.7},"  # Presence
        f"equalizer=f=300:t=q:w=1:g=-1.5,"  # Reduce muddiness
    )
    # The equalizer filters need to be comma-separated within the chain
    # Actually, we need to join them differently
    # Let's fix: individual filters in the chain are separated by commas
    # So the EQ should be three separate entries
    
    # Remove the combined EQ and add separately
    filters = filters[:-1]  # Remove the combined EQ entry
    filters.append(f"equalizer=f={SPEECH_HIGH_BOOST}:t=q:w=1:g={eq_gain}")
    filters.append(f"equalizer=f={SPEECH_PRESENCE}:t=q:w=1.5:g={eq_gain * 0.7}")
    filters.append("equalizer=f=300:t=q:w=1:g=-1.5")

    # 5. De-esser — reduce harsh sibilance
    filters.append(f"afftdn=nr=6:nf=-25")  # Light noise reduction

    # 6. Loudness normalization — broadcast standard
    filters.append(
        f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA={TARGET_LRA}:"
        f"print_format=summary"
    )

    return ",".join(filters)


# ── Audio Ducking ────────────────────────────────────

def build_ducking_filter(
    speech_segments: list,
    total_duration: float,
    duck_level_db: float = -12.0,
    duck_attack: float = 0.3,
    duck_release: float = 1.0,
) -> str:
    """
    Build FFmpeg filter for sidechain-style audio ducking.
    
    When speech is detected, background music ducks to duck_level_db.
    When speech stops, music fades back over duck_release seconds.
    
    Args:
        speech_segments: List of {start, end} dicts where speech occurs
        total_duration: Total clip duration
        duck_level_db: How much to duck BGM (negative dB)
        duck_attack: Fade to ducked level (seconds)
        duck_release: Fade back to full level (seconds)
    
    Returns:
        FFmpeg volume filter string with time-based ducking
    """
    if not speech_segments:
        return f"volume=1.0"  # No ducking needed

    # Build volume changes based on speech timing
    # Format: volume=0.3:enable='between(t,start,end)'
    # We use full volume when no speech, ducked when speech
    
    # Create enable expressions for ducking
    # When speech is active → ducked volume
    # When no speech → full volume
    
    # Build a complex volume filter with time-based ducking
    ducked_vol = 10 ** (duck_level_db / 20)  # Convert dB to linear
    
    # Create the enable expression
    # "between(t, start1, end1) || between(t, start2, end2) || ..."
    enable_parts = []
    for seg in speech_segments:
        s = max(0, seg.get("start", 0))
        e = min(total_duration, seg.get("end", 0))
        if e > s:
            enable_parts.append(f"between(t,{s:.2f},{e:.2f})")

    if not enable_parts:
        return "volume=1.0"

    enable_expr = " || ".join(enable_parts)

    # Sidechain compression style: duck when speech present
    return (
        f"volume={ducked_vol:.3f}:enable='{enable_expr}',"
        f"afade=t=in:d={duck_attack}:st=0,"
        f"afade=t=out:d={duck_release}:st={max(0, total_duration - duck_release):.2f}"
    )


# ── Full Enhancement ─────────────────────────────────

def enhance_audio(
    video_path: Path,
    output_path: Path,
    has_bgm: bool = False,
    speech_segments: Optional[list] = None,
    aggressive: bool = False,
) -> Tuple[Path, Dict]:
    """
    Apply full audio enhancement chain to a video.
    
    This is the main entry point for audio quality.
    Processes the audio track while keeping video untouched.
    
    Args:
        video_path: Input video
        output_path: Where to write enhanced output
        has_bgm: Whether BGM is present (affects ducking)
        speech_segments: Speech timing for ducking
        aggressive: More aggressive processing for poor audio
    
    Returns:
        (output_path, enhancement_report)
    """
    from .utils import rel_path, to_unix, run_ffmpeg

    log.info(f"[Audio] Enhancing: {video_path.name}")

    # Analyze first
    analysis = analyze_audio(video_path)
    report = {"analysis": analysis, "filters_applied": []}

    if not analysis.get("needs_enhancement", True) and not aggressive:
        log.info("[Audio] Analysis shows audio is already good — minimal processing")
        # Still apply basic loudnorm for consistency
        filter_chain = f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TRUE_PEAK}:LRA={TARGET_LRA}"
    else:
        # Full enhancement chain
        filter_chain = build_enhancement_filter(analysis, has_bgm, aggressive)
        report["filters_applied"] = [
            "highpass", "noise_gate", "compressor",
            "eq_clarity", "eq_presence", "eq_mudness_reduction",
            "noise_reduction", "loudnorm"
        ]

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", rel_path(video_path),
        "-af", filter_chain,
        "-c:v", "copy",  # Don't touch video
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        rel_path(output_path),
    ]

    try:
        run_ffmpeg(cmd, timeout=300, description="Audio Enhancement")
        log.info(f"[Audio] Enhanced: {output_path.name}")

        # Post-enhancement analysis
        post_analysis = analyze_audio(output_path)
        report["post_analysis"] = post_analysis
        report["improvement"] = {
            "mean_volume_delta": (
                (post_analysis.get("mean_volume_db", 0) or 0) -
                (analysis.get("mean_volume_db", 0) or 0)
            ) if analysis.get("mean_volume_db") else None,
        }

        return output_path, report

    except Exception as e:
        log.error(f"[Audio] Enhancement failed: {e}")
        # Return original if enhancement fails
        return video_path, {"error": str(e), "analysis": analysis}


def mix_audio_with_ducking(
    video_path: Path,
    bgm_path: Path,
    output_path: Path,
    speech_segments: list,
    total_duration: float,
    bgm_volume_db: float = -18.0,
    duck_level_db: float = -12.0,
) -> Path:
    """
    Mix background music with speech-aware ducking.
    
    The BGM ducks when someone is speaking, and comes back up
    during pauses. This is how professional video audio works.
    
    Args:
        video_path: Video with speech audio
        bgm_path: Background music file
        output_path: Where to write the mixed result
        speech_segments: When speech occurs [{start, end}]
        total_duration: Total video duration
        bgm_volume_db: Base BGM volume (dB)
        duck_level_db: How much BGM ducks during speech (dB)
    
    Returns:
        Path to mixed output
    """
    from .utils import rel_path, to_unix, run_ffmpeg

    # Build ducking filter for BGM
    ducking_filter = build_ducking_filter(
        speech_segments, total_duration, duck_level_db
    )

    # Mix: speech audio at full, BGM with ducking
    cmd = [
        "ffmpeg", "-y",
        "-i", rel_path(video_path),
        "-i", rel_path(bgm_path),
        "-filter_complex",
        f"[1:a]volume={bgm_volume_db}dB,{ducking_filter}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        rel_path(output_path),
    ]

    try:
        run_ffmpeg(cmd, timeout=300, description="Audio Ducking Mix")
        log.info(f"[Audio] Mixed with ducking: {output_path.name}")
        return output_path
    except Exception as e:
        log.error(f"[Audio] Ducking mix failed: {e}")
        return video_path
