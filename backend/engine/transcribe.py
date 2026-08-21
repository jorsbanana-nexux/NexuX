"""
NexuX V8.0 — Transcription Engine
===================================================
faster-whisper (primary, in requirements.txt) + whisperx fallback.
Word-level timestamps, speaker diarization, language detection.
"""
import json, os
from pathlib import Path
from typing import Optional, Dict
import logging

from .constants import OUTPUT_DIR
from .utils import clean_for_json, get_device

log = logging.getLogger("nexus.transcribe")


def transcribe(
    video_path: Path,
    job_id: str,
    language: Optional[str] = None,
    diarization: bool = True,
    model_size: Optional[str] = None,
) -> Dict:
    """Transcribe video audio to text with word-level timestamps.
    
    Tries faster-whisper first (already in requirements.txt).
    Falls back to whisperx if installed (adds diarization).
    Falls back to openai-whisper if installed.
    
    Args:
        video_path: Path to video file
        job_id: Job identifier for saving transcript
        language: Force language code (e.g. 'en', 'id', 'es')
        diarization: Whether to attempt speaker identification
        model_size: Whisper model size override
    
    Returns:
        Transcript dict with segments containing word-level timestamps
    """
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    device = get_device()
    model = model_size or os.environ.get("WHISPER_MODEL", "large-v3")
    
    # ── Try faster-whisper (primary, in requirements.txt) ──
    try:
        result = _transcribe_faster_whisper(video_path, device, model, language)
        if result:
            # Try diarization with whisperx if requested and available
            if diarization:
                result = _try_diarization(video_path, result, device)
            _save(result, job_id)
            return result
    except Exception as e:
        log.warning(f"[Transcribe] faster-whisper failed: {e}")
    
    # ── Fallback: whisperx (if installed separately) ──
    try:
        result = _transcribe_whisperx(video_path, device, model, language, diarization)
        if result:
            _save(result, job_id)
            return result
    except Exception as e:
        log.warning(f"[Transcribe] whisperx failed: {e}")
    
    # ── Fallback: openai-whisper (if installed separately) ──
    result = _transcribe_whisper(video_path, device, model, language)
    _save(result, job_id)
    return result


def _transcribe_faster_whisper(
    video_path: Path, device: str, model_size: str,
    language: Optional[str],
) -> Optional[Dict]:
    """Transcribe using faster-whisper (already in requirements.txt)."""
    from faster_whisper import WhisperModel
    
    log.info(f"[faster-whisper] Loading {model_size} on {device}...")
    compute = "float16" if device == "cuda" else "int8"
    
    model = WhisperModel(model_size, device=device, compute_type=compute)
    
    beam = 5
    opts = {
        "word_timestamps": True,
        "beam_size": beam,
        "vad_filter": True,
    }
    if language:
        opts["language"] = language
    
    segments_gen, info = model.transcribe(str(video_path), **opts)
    detected_lang = info.language if hasattr(info, "language") else "?"
    log.info(f"[faster-whisper] Language: {detected_lang} (prob: {getattr(info, 'language_probability', 0):.2f})")
    
    # Convert generator to list and normalize format
    segments = []
    for seg in segments_gen:
        words = []
        if hasattr(seg, "words") and seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3) if hasattr(w, "probability") else 1.0,
                })
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words,
        })
    
    log.info(f"[faster-whisper] Transcribed {len(segments)} segments")
    
    return {
        "language": detected_lang,
        "segments": segments,
        "text": " ".join(s["text"] for s in segments),
    }


def _try_diarization(
    video_path: Path, result: Dict, device: str,
) -> Dict:
    """Try to add speaker diarization using whisperx (optional)."""
    try:
        import whisperx
        
        log.info("[Diarization] Attempting speaker identification via whisperx...")
        hf_token = os.environ.get("HF_TOKEN", "")
        diarize_model = whisperx.DiarizationPipeline(
            use_auth_token=hf_token or None, device=device)
        audio = whisperx.load_audio(str(video_path))
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        
        speakers = set(
            s.get("speaker", "SPEAKER_00")
            for s in result.get("segments", []))
        log.info(f"[Diarization] Speakers detected: {len(speakers)}")
    except ImportError:
        log.info("[Diarization] whisperx not installed, skipping speaker identification")
    except Exception as e:
        log.warning(f"[Diarization] Failed: {e}")
    
    return result


def _transcribe_whisperx(
    video_path: Path, device: str, model_size: str,
    language: Optional[str], diarization: bool,
) -> Optional[Dict]:
    """Transcribe using whisperx (optional, requires separate install)."""
    import whisperx
    
    log.info(f"[WhisperX] Loading {model_size} on {device}...")
    compute = "float16" if device == "cuda" else "int8"
    model = whisperx.load_model(model_size, device, compute_type=compute)
    
    audio = whisperx.load_audio(str(video_path))
    result = model.transcribe(audio, batch_size=16, language=language)
    detected_lang = result.get("language", "?")
    log.info(f"[WhisperX] Language: {detected_lang}")
    
    # Word alignment
    try:
        model_a, metadata = whisperx.load_align_model(
            language_code=detected_lang, device=device)
        result = whisperx.align(
            result["segments"], model_a, metadata, audio, device,
            return_char_alignments=False)
    except Exception as e:
        log.warning(f"[WhisperX] Alignment failed: {e}")
    
    # Speaker diarization
    if diarization:
        try:
            hf_token = os.environ.get("HF_TOKEN", "")
            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=hf_token or None, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            speakers = set(
                s.get("speaker", "SPEAKER_00")
                for s in result.get("segments", []))
            log.info(f"[WhisperX] Speakers detected: {len(speakers)}")
        except Exception as e:
            log.warning(f"[WhisperX] Diarization skipped: {e}")
    
    return result


def _transcribe_whisper(
    video_path: Path, device: str, model_size: str,
    language: Optional[str],
) -> Dict:
    """Transcribe using openai-whisper (optional, requires separate install)."""
    import whisper
    
    log.info(f"[Whisper] Loading {model_size} on {device}...")
    model = whisper.load_model(model_size, device=device)
    
    opts = {"word_timestamps": True, "verbose": False}
    if language:
        opts["language"] = language
    
    result = model.transcribe(str(video_path), **opts)
    log.info(f"[Whisper] Language: {result.get('language', '?')}")
    return result


def _save(result: dict, job_id: str):
    """Save transcript to JSON file."""
    path = OUTPUT_DIR / job_id / "transcript.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean_for_json(result), f, indent=2, ensure_ascii=False)
    
    segments = len(result.get("segments", []))
    log.info(f"[Transcribe] Saved: {path.name} ({segments} segments)")
