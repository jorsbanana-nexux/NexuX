"""
NexuX V9.7 — Transcription Engine (WhisperX only)
===================================================
faster-whisper / openai-whisper have been REMOVED. WhisperX is the single
transcription backend — it wraps faster-whisper under the hood and adds
word-level alignment + optional speaker diarization.

Model selection comes from the persistent settings store
(utils/settings_store), not raw env vars — the Settings UI writes the
file, and every transcription reads it fresh. This fixes the bug where
the engine kept loading large-v3 even after the user changed the model.

WhisperX is imported lazily — if it's not importable, we fail with a
clear error instead of hanging on a CPU model load.
"""
import json, os
from pathlib import Path
from typing import Optional, Dict, List
import logging

from .constants import OUTPUT_DIR
from .utils import clean_for_json, get_device
from utils import settings_store

log = logging.getLogger("nexus.transcribe")


def transcribe(
    video_path: Path,
    job_id: str,
    language: Optional[str] = None,
    diarization: Optional[bool] = None,
    model_size: Optional[str] = None,
) -> Dict:
    """Transcribe video audio to text with word-level timestamps via WhisperX.

    Args:
        video_path: Path to video/audio file (whisperx.load_audio handles both)
        job_id: Job identifier for saving transcript
        language: Force language code; None = read from settings (auto-detect)
        diarization: Override settings toggle (requires HF_TOKEN for pyannote)
        model_size: Override settings model (see settings_store.MODEL_VARIANTS)

    Returns:
        Transcript dict with segments containing word-level timestamps
    """
    try:
        import whisperx  # noqa: F401 — presence check only
    except ImportError:
        raise RuntimeError("WhisperX is not installed. Run: pip install whisperx")

    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    device = get_device()
    model = model_size or settings_store.get("transcription_model", "small")
    lang = language if language is not None else settings_store.get("language")
    do_diarize = settings_store.get("diarization", False) if diarization is None else diarization
    batch = settings_store.get("batch_size", 16) or 16

    result = _transcribe_whisperx(video_path, device, model, lang, do_diarize, batch)
    _save(result, job_id)
    return result


def _transcribe_whisperx(
    video_path: Path, device: str, model_size: str,
    language: Optional[str], diarization: bool, batch_size: int,
) -> Dict:
    import whisperx

    log.info(f"[WhisperX] Loading {model_size} on {device} (batch={batch_size})...")
    compute = "float16" if device == "cuda" else "int8"
    model = whisperx.load_model(model_size, device, compute_type=compute)

    audio = whisperx.load_audio(str(video_path))
    kwargs = {"batch_size": batch_size}
    if language:
        kwargs["language"] = language
    result = model.transcribe(audio, **kwargs)

    detected_lang = result.get("language", language or "?")
    log.info(f"[WhisperX] Language: {detected_lang}")

    # Word-level alignment (karaoke-quality timing)
    if settings_store.get("word_timestamps", True):
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=detected_lang, device=device)
            result = whisperx.align(
                result["segments"], model_a, metadata, audio, device,
                return_char_alignments=False)
        except Exception as e:
            log.warning(f"[WhisperX] Alignment skipped: {e}")

    # Speaker diarization (opt-in, needs HF_TOKEN for pyannote)
    if diarization:
        try:
            hf_token = os.environ.get("HF_TOKEN", "")
            if not hf_token:
                log.warning("[WhisperX] Diarization requested but HF_TOKEN is empty — skipping.")
            else:
                diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=hf_token, device=device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                speakers = set(
                    s.get("speaker", "SPEAKER_00")
                    for s in result.get("segments", []))
                log.info(f"[WhisperX] Speakers detected: {len(speakers)}")
        except Exception as e:
            log.warning(f"[WhisperX] Diarization failed: {e}")

    # Normalize to the segment/words shape the pipeline expects.
    segments: List[Dict] = []
    for seg in result.get("segments", []):
        words = []
        for w in seg.get("words", []) or []:
            w_dict = {
                "word": w.get("word", "").strip(),
                "start": round(w.get("start", 0), 3),
                "end": round(w.get("end", 0), 3),
                "probability": round(w.get("score", w.get("probability", 1)), 3),
            }
            if "speaker" in w:
                w_dict["speaker"] = w["speaker"]
            words.append(w_dict)
        seg_dict = {
            "start": round(seg.get("start", 0), 3),
            "end": round(seg.get("end", 0), 3),
            "text": seg.get("text", "").strip(),
            "words": words,
        }
        if "speaker" in seg:
            seg_dict["speaker"] = seg["speaker"]
        segments.append(seg_dict)

    log.info(f"[WhisperX] Transcribed {len(segments)} segments")
    return {
        "language": detected_lang,
        "segments": segments,
        "text": " ".join(s["text"] for s in segments),
    }


def _save(result: Dict, job_id: str) -> None:
    """Save transcript to JSON for debugging/reuse."""
    try:
        path = OUTPUT_DIR / job_id / "transcript.json"
        path.write_text(json.dumps(clean_for_json(result), indent=2))
        log.info(f"[Transcribe] Saved to {path.name}")
    except Exception as e:
        log.warning(f"[Transcribe] Save failed: {e}")
