"""
NexuX V9.5 — Edge-TTS Voice-Over Engine
==========================================
Dynamic voice-over synthesis with ON/OFF toggle, personalization,
and FFmpeg audio mixing with original audio ducking.
"""
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from .constants import OUTPUT_DIR
from .utils import rel_path, to_unix, run_ffmpeg

log = logging.getLogger("nexus.voiceover")

# ── Voice Catalog & Aliases ──

AVAILABLE_VOICES: List[Dict[str, str]] = [
    {
        "id": "en-US-GuyNeural",
        "alias": "male_narrator",
        "name": "Guy (US Male Narrator)",
        "gender": "male",
        "language": "en-US",
        "style": "Narrator / Professional",
    },
    {
        "id": "en-US-ChristopherNeural",
        "alias": "male_deep",
        "name": "Christopher (US Male Deep)",
        "gender": "male",
        "language": "en-US",
        "style": "Deep / Authoritative",
    },
    {
        "id": "en-US-EricNeural",
        "alias": "male_young",
        "name": "Eric (US Male Young)",
        "gender": "male",
        "language": "en-US",
        "style": "Energetic / Gen Z",
    },
    {
        "id": "en-US-DavisNeural",
        "alias": "gaming",
        "name": "Davis (US Male Gaming)",
        "gender": "male",
        "language": "en-US",
        "style": "Gaming / Casual",
    },
    {
        "id": "en-US-AriaNeural",
        "alias": "female_professional",
        "name": "Aria (US Female)",
        "gender": "female",
        "language": "en-US",
        "style": "Crisp / Professional",
    },
    {
        "id": "en-US-JennyNeural",
        "alias": "female_friendly",
        "name": "Jenny (US Female)",
        "gender": "female",
        "language": "en-US",
        "style": "Warm / Conversational",
    },
    {
        "id": "en-GB-SoniaNeural",
        "alias": "female_british",
        "name": "Sonia (UK Female)",
        "gender": "female",
        "language": "en-GB",
        "style": "British / Elegant",
    },
    {
        "id": "en-GB-RyanNeural",
        "alias": "male_british",
        "name": "Ryan (UK Male)",
        "gender": "male",
        "language": "en-GB",
        "style": "British / Formal",
    },
    {
        "id": "es-ES-ElviraNeural",
        "alias": "spanish_female",
        "name": "Elvira (Spanish Female)",
        "gender": "female",
        "language": "es-ES",
        "style": "Spanish / Clear",
    },
    {
        "id": "es-ES-AlvaroNeural",
        "alias": "spanish_male",
        "name": "Alvaro (Spanish Male)",
        "gender": "male",
        "language": "es-ES",
        "style": "Spanish / Narrator",
    },
    {
        "id": "fr-FR-DeniseNeural",
        "alias": "french_female",
        "name": "Denise (French Female)",
        "gender": "female",
        "language": "fr-FR",
        "style": "French / Smooth",
    },
    {
        "id": "fr-FR-HenriNeural",
        "alias": "french_male",
        "name": "Henri (French Male)",
        "gender": "male",
        "language": "fr-FR",
        "style": "French / Professional",
    },
    {
        "id": "de-DE-KatjaNeural",
        "alias": "german_female",
        "name": "Katja (German Female)",
        "gender": "female",
        "language": "de-DE",
        "style": "German / Clear",
    },
    {
        "id": "de-DE-KillianNeural",
        "alias": "german_male",
        "name": "Killian (German Male)",
        "gender": "male",
        "language": "de-DE",
        "style": "German / Energetic",
    },
    {
        "id": "ja-JP-NanamiNeural",
        "alias": "japanese_female",
        "name": "Nanami (Japanese Female)",
        "gender": "female",
        "language": "ja-JP",
        "style": "Japanese / Natural",
    },
    {
        "id": "ja-JP-KeitaNeural",
        "alias": "japanese_male",
        "name": "Keita (Japanese Male)",
        "gender": "male",
        "language": "ja-JP",
        "style": "Japanese / Clear",
    },
    {
        "id": "zh-CN-XiaoxiaoNeural",
        "alias": "chinese_female",
        "name": "Xiaoxiao (Chinese Female)",
        "gender": "female",
        "language": "zh-CN",
        "style": "Chinese / Expressive",
    },
    {
        "id": "zh-CN-YunjianNeural",
        "alias": "chinese_male",
        "name": "Yunjian (Chinese Male)",
        "gender": "male",
        "language": "zh-CN",
        "style": "Chinese / Narrative",
    },
]

VOICE_ALIASES: Dict[str, str] = {v["alias"]: v["id"] for v in AVAILABLE_VOICES}
VOICE_ALIASES.update({v["id"]: v["id"] for v in AVAILABLE_VOICES})


def get_available_voices() -> List[Dict[str, str]]:
    """Return catalog of available voices for API endpoints."""
    return AVAILABLE_VOICES


def resolve_voice_id(voice_input: Optional[str]) -> str:
    """Resolve a voice alias or ID to an exact Edge TTS voice ID."""
    if not voice_input:
        return "en-US-GuyNeural"
    return VOICE_ALIASES.get(voice_input, voice_input)


def speed_to_edge_rate(speed: float) -> str:
    """Convert speed multiplier (0.5x - 2.0x) to Edge-TTS rate string format (+0%, +20%, -50%)."""
    clamped_speed = max(0.5, min(2.0, float(speed)))
    pct = int(round((clamped_speed - 1.0) * 100))
    return f"{pct:+d}%"


def pitch_to_edge_pitch(pitch: Union[str, float, int, None]) -> str:
    """Convert pitch input to Edge-TTS pitch string (+0Hz, -3Hz, +5Hz)."""
    if pitch is None:
        return "+0Hz"
    if isinstance(pitch, str):
        p_str = pitch.strip()
        if p_str.endswith("Hz") or p_str.endswith("%"):
            return p_str
        try:
            val = float(p_str)
            return f"{int(val):+d}Hz"
        except ValueError:
            return "+0Hz"
    try:
        val = float(pitch)
        return f"{int(val):+d}Hz"
    except (ValueError, TypeError):
        return "+0Hz"


def extract_script_from_transcript(transcript: Dict, clip: Dict) -> str:
    """Extract transcript text corresponding to clip's start and end times."""
    cs = clip.get("start", 0)
    ce = clip.get("end", 0)
    segments = transcript.get("segments", [])
    parts = []

    for seg in segments:
        ss = seg.get("start", 0)
        se = seg.get("end", 0)
        if se >= cs and ss <= ce:
            text = seg.get("text", "").strip()
            if text:
                parts.append(text)

    script = " ".join(parts).strip()
    if not script and clip.get("reason"):
        script = str(clip.get("reason"))
    return script


async def generate_voiceover_audio(
    text: str,
    voice: str = "en-US-GuyNeural",
    speed: float = 1.0,
    pitch: Union[str, float, int] = "+0Hz",
    output_path: Optional[Path] = None,
    job_id: str = "default",
    clip_index: int = 0,
) -> Path:
    """Generate audio file using edge-tts.
    
    Args:
        text: Script text to speak
        voice: Voice ID or alias
        speed: Speed multiplier (0.5x to 2.0x)
        pitch: Pitch adjustment (+0Hz, -3Hz, +5Hz)
        output_path: Destination path for generated audio
        job_id: Job identifier
        clip_index: Index of clip
    
    Returns:
        Path to output audio file
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate voice-over: text is empty")

    voice_id = resolve_voice_id(voice)
    rate_str = speed_to_edge_rate(speed)
    pitch_str = pitch_to_edge_pitch(pitch)

    if not output_path:
        out_dir = OUTPUT_DIR / job_id / "audio"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"vo_{clip_index:02d}.mp3"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import edge_tts
    except ImportError:
        raise RuntimeError("edge-tts library is not installed")

    log.info(f"[Voiceover] Synthesizing speech: voice={voice_id}, rate={rate_str}, pitch={pitch_str}")
    communicate = edge_tts.Communicate(text=text.strip(), voice=voice_id, rate=rate_str, pitch=pitch_str)
    await communicate.save(str(output_path))

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Voice-over synthesis failed: output file missing or empty ({output_path})")

    log.info(f"[Voiceover] Audio created: {output_path.name} ({output_path.stat().st_size} bytes)")
    return output_path


def has_audio_stream(video_path: Path) -> bool:
    """Check if video file has an audio stream using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        rel_path(video_path),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=to_unix(Path.cwd()))
        return "audio" in r.stdout.lower()
    except Exception:
        return True  # Fallback assume True


def mix_voiceover_into_video(
    video_path: Path,
    voiceover_audio_path: Path,
    output_path: Path,
    voice_volume: float = 1.0,
    original_volume: float = 0.2,
) -> Path:
    """Duck original video audio and mix voiceover audio on top.
    
    Args:
        video_path: Source video path
        voiceover_audio_path: Generated voiceover audio MP3/WAV
        output_path: Output video file path
        voice_volume: Voice-over volume multiplier (0.0 to 2.0)
        original_volume: Original video audio volume multiplier (0.0 to 1.0)
    
    Returns:
        Path to output video with mixed audio
    """
    video_rel = rel_path(video_path)
    vo_rel = rel_path(voiceover_audio_path)
    out_rel = rel_path(output_path)

    has_orig_audio = has_audio_stream(video_path)

    if has_orig_audio and original_volume > 0.001:
        # Mix ducked original audio + voiceover
        filter_complex = (
            f"[0:a]volume={original_volume:.2f}[orig];"
            f"[1:a]volume={voice_volume:.2f}[vo];"
            f"[orig][vo]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
    else:
        # Use voiceover as sole audio
        filter_complex = f"[1:a]volume={voice_volume:.2f}[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_rel,
        "-i", vo_rel,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_rel,
    ]

    log.info(f"[Voiceover] Mixing audio into video: original_vol={original_volume:.2f}, vo_vol={voice_volume:.2f}")
    run_ffmpeg(cmd, timeout=300, description="Voice-over Audio Mix")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg audio mixing failed: output missing ({output_path})")

    return output_path


async def process_voiceover_stage(
    video_path: Path,
    job_id: str,
    clip_index: int,
    clip: Dict,
    transcript: Dict,
    config: Dict,
) -> Path:
    """Process voice-over for a rendered clip if voiceover is enabled.
    
    Args:
        video_path: Path to rendered clip
        job_id: Job identifier
        clip_index: Index of clip
        clip: Clip info dict
        transcript: Full transcript dict
        config: Voiceover configuration dict (speed, volume, voice, custom_script, etc.)
    
    Returns:
        Path to processed video (or original video_path if voiceover disabled/failed)
    """
    enabled = config.get("voiceover_enabled", False) or config.get("voice_over", False)
    if not enabled:
        return video_path

    # Voice selection
    voice = config.get("voice") or config.get("voice_style") or "en-US-GuyNeural"
    speed = float(config.get("voice_speed", config.get("speed", 1.0)))
    volume = float(config.get("voice_volume", config.get("volume", 1.0)))
    pitch = config.get("voice_pitch", config.get("voice_tone", config.get("pitch", "+0Hz")))
    orig_vol = float(config.get("original_audio_volume", config.get("original_volume", 0.2)))

    # Script selection: custom script or auto-extracted
    custom_script = config.get("voice_over_text") or config.get("custom_script")
    if custom_script and custom_script.strip():
        script = custom_script.strip()
    else:
        script = extract_script_from_transcript(transcript, clip)

    if not script:
        log.warning(f"[Voiceover] Clip {clip_index}: No text for voice-over. Skipping.")
        return video_path

    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    vo_audio_path = out_dir / "audio" / f"vo_clip_{clip_index:02d}.mp3"
    vo_video_path = out_dir / f"clip_{clip_index:02d}_vo.mp4"

    try:
        # Step 1: Synthesize TTS
        await generate_voiceover_audio(
            text=script,
            voice=voice,
            speed=speed,
            pitch=pitch,
            output_path=vo_audio_path,
            job_id=job_id,
            clip_index=clip_index,
        )

        # Step 2: Mix with video
        mixed_path = mix_voiceover_into_video(
            video_path=video_path,
            voiceover_audio_path=vo_audio_path,
            output_path=vo_video_path,
            voice_volume=volume,
            original_volume=orig_vol,
        )

        log.info(f"[Voiceover] Clip {clip_index} voice-over complete: {mixed_path.name}")
        return mixed_path

    except Exception as e:
        log.error(f"[Voiceover] Clip {clip_index} voice-over failed: {e}. Falling back to original video.")
        return video_path
