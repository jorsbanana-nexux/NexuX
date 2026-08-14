"""
Nexus-Clipper AI Ultra v3.0 — Engine (PRODUCTION)
===================================================
yt-dlp -> WhisperX -> MediaPipe -> FFmpeg
+ Audio BGM mixing, normalization
+ Ken Burns auto-zoom, color grading
+ Retry logic, structured logging
+ Multi-platform aspect ratios
"""
import os, sys, json, math, time, shutil
import subprocess, tempfile, random
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from functools import lru_cache
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("engine")

OUTPUT_DIR = Path(os.environ.get("NEXUS_OUTPUT_DIR", "output"))
ASSETS_DIR = Path(os.environ.get("NEXUS_ASSETS_DIR", "assets"))
TEMP_DIR = Path(tempfile.gettempdir()) / "nexus-clipper"

for d in [OUTPUT_DIR, ASSETS_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = 3
DOWNLOAD_TIMEOUT = 600
RENDER_TIMEOUT = 900

ASPECT_RATIOS = {
    "9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080),
    "4:5": (1080, 1350), "2:3": (1080, 1620), "21:9": (1920, 822),
}

VIDEO_CODECS = {
    "h264": {"codec": "libx264", "crf": "23", "preset": "medium"},
    "h265": {"codec": "libx265", "crf": "28", "preset": "medium"},
}

print("Engine v3 module loaded successfully.")

# ===== UTILITIES =====

def _to_unix(p) -> str:
    return str(p).replace("\\", "/")

def _rel_path(p) -> str:
    p_str = _to_unix(p)
    cwd_str = _to_unix(Path.cwd())
    try:
        return str(Path(p_str).relative_to(Path(cwd_str))).replace("\\", "/")
    except ValueError:
        return p_str

def _fmt_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

def _retry(func, *args, max_retries=MAX_RETRIES, **kwargs):
    last_err = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            log.warning(f"Retry {attempt+1}/{max_retries}: {e}. Waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"All {max_retries} attempts failed. Last: {last_err}")

def _detect_gpu() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def _clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj

@lru_cache(maxsize=1)
def _check_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("FFmpeg not found! Install: apt install ffmpeg")
    return ff

@lru_cache(maxsize=1)
def _check_ffprobe() -> str:
    fp = shutil.which("ffprobe")
    if not fp:
        raise RuntimeError("FFprobe not found! Install: apt install ffmpeg")
    return fp


# ===== STAGE 1: DOWNLOAD =====

def download_youtube(url: str, job_id: str) -> Path:
    """Download YouTube video. Returns path to video file."""
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    tmpl = str(work_dir / "%(title).100s.%(ext)s")
    cmd = [
        "yt-dlp", "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", tmpl, "--no-playlist", "--retries", "10",
        "--socket-timeout", "30", url,
    ]
    def _dl():
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT)
        if r.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {r.stderr[-400:]}")
        for ext in [".mp4", ".mkv", ".webm", ".mov"]:
            files = sorted(work_dir.glob(f"*{ext}"), key=lambda p: p.stat().st_size, reverse=True)
            if files:
                return files[0]
        raise FileNotFoundError(f"No video found in {work_dir}")
    return _retry(_dl)

def get_video_info(url: str) -> Dict:
    """Get video metadata without downloading."""
    cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp info failed: {r.stderr[-300:]}")
    info = json.loads(r.stdout)
    return {
        "title": info.get("title", ""),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "resolution": f"{info.get('width',0)}x{info.get('height',0)}",
        "fps": info.get("fps", 30),
    }

# ===== STAGE 2: TRANSCRIBE =====

def transcribe_video(video_path: Path, job_id: str,
                     language: Optional[str] = None,
                     enable_diarization: bool = True) -> dict:
    """Transcribe audio with WhisperX (fallback: openai-whisper)."""
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if _detect_gpu() else "cpu"
    model_size = os.environ.get("WHISPER_MODEL", "large-v3")

    # Try WhisperX
    try:
        import whisperx
        log.info(f"[Transcribe] WhisperX on {device} ({model_size})")
        asr_opts = {"compute_type": "float16" if device == "cuda" else "int8"}
        model = whisperx.load_model(model_size, device, **asr_opts)
        audio = whisperx.load_audio(str(video_path))
        result = model.transcribe(audio, batch_size=16, language=language)
        lang = result.get("language", "?")
        log.info(f"[WhisperX] Language: {lang}")

        model_a, metadata = whisperx.load_align_model(language_code=lang, device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device,
                                return_char_alignments=False)

        if enable_diarization:
            try:
                hf_token = os.environ.get("HF_TOKEN", "")
                diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=hf_token or None, device=device)
                diarize_segments = diarize_model(audio)
                result = whisperx.assign_word_speakers(diarize_segments, result)
                speakers = set(s.get("speaker", "SPEAKER_00")
                               for s in result.get("segments", []))
                log.info(f"[WhisperX] Speakers: {len(speakers)}")
            except Exception as e:
                log.warning(f"[WhisperX] Diarization skip: {e}")

        _save_transcript(result, job_id)
        return result
    except Exception as e:
        log.warning(f"[WhisperX] Failed ({e}), fallback to openai-whisper...")

    # Fallback
    import whisper
    log.info(f"[Whisper] Loading {model_size} on {device}...")
    model = whisper.load_model(model_size, device=device)
    opts = {"word_timestamps": True, "verbose": False}
    if language:
        opts["language"] = language
    result = model.transcribe(str(video_path), **opts)
    _save_transcript(result, job_id)
    return result

def _save_transcript(result: dict, job_id: str):
    p = OUTPUT_DIR / job_id / "transcript.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(_clean_for_json(result), f, indent=2, ensure_ascii=False)
    log.info(f"[Transcribe] Saved: {p}")


# ===== STAGE 3: FACE DETECTION =====

def analyze_faces(video_path: Path, job_id: str,
                  sample_every_n_frames: int = 15) -> List[Dict]:
    """Detect faces using MediaPipe. Returns face tracking data."""
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        log.warning("[FaceTrack] OpenCV/MediaPipe not installed. Skipping.")
        return []

    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    mp_face = mp.solutions.face_detection
    face_detection = mp_face.FaceDetection(
        model_selection=1, min_detection_confidence=0.5)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log.warning(f"[FaceTrack] Cannot open: {video_path}")
        face_detection.close()
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info(f"[FaceTrack] {fps:.1f}fps, {total_frames} frames")

    face_data = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every_n_frames == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(frame_rgb)
            faces = []
            if results.detections:
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    faces.append({
                        "x": max(0.0, bbox.xmin),
                        "y": max(0.0, bbox.ymin),
                        "w": min(1.0, max(0.0, bbox.width)),
                        "h": min(1.0, max(0.0, bbox.height)),
                        "score": float(det.score[0]) if det.score else 1.0,
                    })
            face_data.append({
                "time": round(frame_idx / fps, 2),
                "frame": frame_idx,
                "faces": faces,
                "video_w": width,
                "video_h": height,
            })
        frame_idx += 1

    cap.release()
    face_detection.close()

    fpath = work_dir / "face_tracking.json"
    with open(fpath, "w") as f:
        json.dump(face_data, f, indent=2)

    faces_detected = sum(1 for fd in face_data if fd["faces"])
    log.info(f"[FaceTrack] Done: {len(face_data)} samples, {faces_detected} with faces")
    return face_data


# ===== STAGE 4: CONTENT ANALYSIS =====

EXCITEMENT_KEYWORDS = [
    "wow", "amazing", "incredible", "crazy", "secret", "never",
    "shocking", "unbelievable", "insane", "game changer",
    "mengerikan", "rahasia", "gila", "aneh", "menakjubkan",
    "viral", "fenomenal", "terbongkar", "fakta", "misteri",
    "ternyata", "buset", "anjir", "edan", "mind-blowing",
    "exposed", "breakthrough", "membongkar", "nggak nyangka",
    "plot twist", "the truth", "real reason", "nobody knows",
]

def analyze_content(transcript: dict, target_duration: int = 60,
                    face_data: Optional[List[Dict]] = None,
                    max_clips: int = 10) -> list:
    """Find most 'viral' clip candidates from transcript."""
    segments = transcript.get("segments", [])
    if not segments:
        log.warning("[Analyze] No segments in transcript")
        return []

    # Get total duration
    try:
        total_duration = float(
            segments[-1].get("end") or segments[-1].get("start", 0) + 5)
    except (IndexError, KeyError, TypeError):
        log.error("[Analyze] Could not determine video duration")
        return []

    log.info(f"[Analyze] Duration: {total_duration:.1f}s, target: {target_duration}s")

    # Short video -> single full clip
    if total_duration <= target_duration:
        full_text = " ".join(s.get("text", "") for s in segments)
        word_count = len(full_text.split())
        return [{
            "start": 0, "end": total_duration, "score": 1.0,
            "text": full_text[:300],
            "wps": round(word_count / max(total_duration, 1), 2),
            "keywords": 0, "speakers": 1, "face_visible": 0.0,
            "type": "full_video",
        }]

    # Windowed scanning
    window = target_duration
    step = max(1, target_duration // 4)  # 75% overlap
    clips = []

    start = 0.0
    while start + min(10, target_duration // 2) <= total_duration:
        end = min(start + window, total_duration)
        win_segs = [
            s for s in segments
            if s.get("start", 0) < end and s.get("end", 0) > start
        ]
        if len(win_segs) < 2:
            start += step
            continue

        total_words = sum(len(s.get("text", "").split()) for s in win_segs)
        win_dur = end - start
        wps = total_words / max(win_dur, 1)

        full_lower = " ".join(s.get("text", "") for s in win_segs).lower()
        kw_hits = sum(1 for kw in EXCITEMENT_KEYWORDS if kw in full_lower)

        win_speakers = set(
            s.get("speaker", "SPEAKER_00")
            for s in win_segs if s.get("speaker"))
        speaker_count = len(win_speakers)

        face_vis = 0.0
        if face_data:
            relevant = [fd for fd in face_data if start <= fd["time"] <= end]
            if relevant:
                face_vis = sum(
                    1 for fd in relevant if fd.get("faces")
                ) / len(relevant)

        # Position bonus: later clips slightly favored (revelations)
        position_bonus = 1.0 + (start / max(total_duration, 1)) * 0.3

        # Composite viral score
        score = (
            wps * 0.30 +
            (1.0 + kw_hits * 0.60) * 0.25 +
            (1.0 + speaker_count * 0.30) * 0.15 +
            (1.0 + face_vis * 0.50) * 0.15 +
            position_bonus * 0.15
        )

        clip_text = " ".join(s.get("text", "") for s in win_segs)

        clips.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "score": round(score, 3),
            "text": clip_text[:300],
            "wps": round(wps, 2),
            "keywords": kw_hits,
            "speakers": speaker_count,
            "face_visible": round(face_vis, 2),
            "word_count": total_words,
            "duration": round(win_dur, 1),
        })
        start += step

    if not clips:
        log.warning("[Analyze] No clips found — using full video")
        full_text = " ".join(s.get("text", "") for s in segments)
        return [{
            "start": 0, "end": total_duration, "score": 1.0,
            "text": full_text[:300],
            "wps": round(len(full_text.split()) / max(total_duration, 1), 2),
            "keywords": 0, "speakers": 1, "face_visible": 0.0,
        }]

    # Sort and deduplicate
    clips.sort(key=lambda x: x["score"], reverse=True)
    taken_ranges: List[Tuple[float, float]] = []
    result = []

    for c in clips:
        overlaps = any(
            not (c["end"] <= t[0] or c["start"] >= t[1])
            for t in taken_ranges)
        if overlaps:
            continue
        taken_ranges.append((c["start"], c["end"]))
        result.append(c)
        if len(result) >= max_clips:
            break

    log.info(f"[Analyze] Selected {len(result)} clips (from {len(clips)} candidates)")
    return result


# ===== STAGE 5: RENDER =====

STYLE_PRESETS = {
    "hormozi": {"font":"Arial","font_size":52,"primary":"#FFFFFF","highlight":"#FFD700",
        "stroke":"#000000","position":"center","animation":"pop","stroke_width":3,
        "bold":True,"highlight_words":True},
    "mrbeast": {"font":"Impact","font_size":56,"primary":"#FFFFFF","highlight":"#00FF88",
        "stroke":"#000000","position":"center","animation":"pop_fast","stroke_width":6,
        "bold":True,"highlight_words":True},
    "minimalist": {"font":"Helvetica","font_size":34,"primary":"#CCCCCC","highlight":"#FFFFFF",
        "stroke":"#000000","position":"bottom","animation":"none","stroke_width":1,
        "bold":False,"highlight_words":False},
    "gaming": {"font":"Impact","font_size":58,"primary":"#FF4444","highlight":"#FFFF00",
        "stroke":"#000000","position":"center","animation":"bounce","stroke_width":5,
        "bold":True,"highlight_words":True},
    "cinematic": {"font":"Georgia","font_size":44,"primary":"#EEEEFF","highlight":"#8888FF",
        "stroke":"#000011","position":"bottom","animation":"fade_slow","stroke_width":4,
        "bold":False,"highlight_words":False},
    "neon": {"font":"Arial","font_size":48,"primary":"#FF00FF","highlight":"#00FFFF",
        "stroke":"#4A0072","position":"center","animation":"flicker","stroke_width":3,
        "bold":True,"highlight_words":True},
    "typewriter": {"font":"Courier New","font_size":44,"primary":"#88FF88","highlight":"#AAFFAA",
        "stroke":"#003300","position":"bottom","animation":"typewriter","stroke_width":2,
        "bold":False,"highlight_words":False},
    "tiktok_viral": {"font":"Arial","font_size":50,"primary":"#FF6600","highlight":"#FFD700",
        "stroke":"#000000","position":"random","animation":"pop","stroke_width":4,
        "bold":True,"highlight_words":True},
    "documentary": {"font":"Georgia","font_size":38,"primary":"#DDCCAA","highlight":"#FFEEDD",
        "stroke":"#1A1A0A","position":"bottom","animation":"fade_slow","stroke_width":2,
        "bold":False,"highlight_words":False},
    "comedy": {"font":"Comic Sans MS","font_size":48,"primary":"#FFCC00","highlight":"#FF6600",
        "stroke":"#000000","position":"center","animation":"bounce","stroke_width":3,
        "bold":True,"highlight_words":True},
    "horror": {"font":"Impact","font_size":52,"primary":"#FF0000","highlight":"#FF4444",
        "stroke":"#330000","position":"center","animation":"flicker","stroke_width":5,
        "bold":True,"highlight_words":True},
    "motivational": {"font":"Helvetica","font_size":46,"primary":"#FFFFFF","highlight":"#EEEEEE",
        "stroke":"#000000","position":"center","animation":"slow_reveal","stroke_width":3,
        "bold":True,"highlight_words":False},
    "educational": {"font":"Verdana","font_size":40,"primary":"#66BBFF","highlight":"#FFD700",
        "stroke":"#0D47A1","position":"top","animation":"fade","stroke_width":2,
        "bold":False,"highlight_words":True},
    "podcast": {"font":"Helvetica","font_size":38,"primary":"#FFFFFF","highlight":"#00D4AA",
        "stroke":"#0A0A2E","position":"bottom","animation":"fade","stroke_width":3,
        "bold":False,"highlight_words":True},
}

SPEAKER_COLORS = [
    "#FFFFFF","#FFD700","#00FF88","#FF6B6B","#82B1FF","#E040FB",
    "#FF9100","#00E5FF","#FF4081","#B2FF59","#7C4DFF","#FFD740"]

def _resolve_style(style_config: dict) -> dict:
    stype = style_config.get("subtitle_style", "hormozi")
    preset = STYLE_PRESETS.get(stype, STYLE_PRESETS["hormozi"])
    if stype == "custom":
        return {
            "font": style_config.get("font", "Arial"),
            "font_size": style_config.get("font_size", 48),
            "primary": style_config.get("primary_color", "#FFFFFF"),
            "highlight": style_config.get("highlight_color", "#FFD700"),
            "stroke": style_config.get("stroke_color", "#000000"),
            "position": style_config.get("position", "center"),
            "animation": style_config.get("animation", "pop"),
            "stroke_width": style_config.get("stroke_width", 3),
            "bold": True,
            "highlight_words": style_config.get("highlight_active_word", True),
        }
    result = dict(preset)
    overrides = [("font","font"),("font_size","font_size"),("primary","primary_color"),
        ("highlight","highlight_color"),("stroke","stroke_color"),
        ("position","position"),("animation","animation"),("stroke_width","stroke_width")]
    for pk, ck in overrides:
        if ck in style_config and style_config[ck]:
            result[pk] = style_config[ck]
    return result

def _anim_tag(anim_type: str, word_index: int = 0) -> str:
    return {
        "pop": "{\\t(0,100,\\fscx120\\fscy120)\\t(100,200,\\fscx100\\fscy100)}",
        "pop_fast": "{\\t(0,65,\\fscx125\\fscy125)\\t(65,130,\\fscx100\\fscy100)}",
        "fade": "{\\fade(100,100)}",
        "fade_slow": "{\\fade(400,400)}",
        "bounce": "{\\t(0,80,\\fscx130\\fscy130)\\t(80,150,\\fscx85\\fscy85)\\t(150,200,\\fscx100\\fscy100)}",
        "flicker": "{\\t(0,50,\\alpha&HFF&)\\t(50,100,\\alpha&H00&)\\t(100,130,\\alpha&H80&)\\t(130,160,\\alpha&H00&)}",
        "slow_reveal": "{\\fade(600,600)}",
        "typewriter": f"{{\\fade({word_index*50+100},{word_index*50+100})}}",
        "none": "",
    }.get(anim_type, "")

def _sub_position(pos: str, _w: int, _h: int) -> dict:
    positions = {"top":{"align":8,"marv":60},"center":{"align":5,"marv":40},"bottom":{"align":2,"marv":80}}
    if pos == "random": pos = random.choice(["top","center","bottom"])
    return positions.get(pos, positions["center"])

def _hex_to_ass(h: str) -> str:
    h = h.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}"

def _build_ass(transcript, clip, style_config, job_id, idx, face_data, tw, th) -> Path:
    """Build ASS subtitle file with dynamic per-speaker styling."""
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    p = work_dir / f"sub_{idx:02d}.ass"

    s = _resolve_style(style_config)
    pc = _sub_position(s["position"], tw, th)
    speaker_idx = {}
    speakers_seen = []

    pri = _hex_to_ass(s["primary"])
    hl = _hex_to_ass(s["highlight"])
    sk = _hex_to_ass(s["stroke"])
    bold = 1 if s["bold"] else 0
    sw = s["stroke_width"]
    al = pc["align"]
    mv = pc["marv"]

    # ASS Header
    lines = [
        "[Script Info]",
        "Title: Nexus-Clipper AI v3",
        "ScriptType: v4.00+", "WrapStyle: 0", "ScaledBorderAndShadow: yes",
        f"PlayResX: {tw}", f"PlayResY: {th}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
    ]

    # Default & Highlight styles
    lines.append(
        f"Style: Default,{s['font']},{s['font_size']},{pri},{pri},{sk},{sk},"
        f"{bold},0,0,0,100,100,0,0,1,{sw},2,{al},80,80,{mv},1")
    lines.append(
        f"Style: Highlight,{s['font']},{s['font_size']+6},{hl},{hl},{sk},{sk},"
        f"{bold},0,0,0,100,100,0,0,1,{sw},4,{al},80,80,{mv},1")

    # Per-speaker styles
    for i, spc in enumerate(SPEAKER_COLORS):
        sp_ass = _hex_to_ass(spc)
        lines.append(
            f"Style: Speaker{i},{s['font']},{s['font_size']},{sp_ass},{sp_ass},{sk},{sk},"
            f"{bold},0,0,0,100,100,0,0,1,{sw},2,{al},80,80,{mv},1")
        lines.append(
            f"Style: Speaker{i}H,{s['font']},{s['font_size']+6},{sp_ass},{sp_ass},{sk},{sk},"
            f"{bold},0,0,0,100,100,0,0,1,{sw},4,{al},80,80,{mv},1")

    lines.extend(["", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"])

    cs, ce = clip["start"], clip["end"]
    word_counter = 0

    for seg in transcript.get("segments", []):
        try:
            ss = float(seg.get("start", 0))
            se = float(seg.get("end", 0))
        except (TypeError, ValueError):
            continue
        if se < cs or ss > ce:
            continue

        spk = seg.get("speaker", "SPEAKER_00")
        if spk not in speaker_idx:
            speaker_idx[spk] = len(speakers_seen) % len(SPEAKER_COLORS)
            speakers_seen.append(spk)
        si = speaker_idx[spk]

        words = seg.get("words", [])
        if not words:
            ls = max(0, ss - cs)
            le = se - cs
            text = seg.get("text", "").strip().replace("\n", "\\N")
            tag = _anim_tag(s["animation"])
            sty = f"Speaker{si}H" if s["highlight_words"] else f"Speaker{si}"
            lines.append(f"Dialogue: 0,{_fmt_time(ls)},{_fmt_time(le)},{sty},,0,0,0,,{tag}{text}")
            continue

        for w in words:
            try:
                ws = float(w.get("start", ss))
                we = float(w.get("end", se))
            except (TypeError, ValueError):
                ws, we = ss, se
            if we < cs or ws > ce:
                continue
            ls = max(0, ws - cs)
            le = min(we - cs, ce - cs)
            txt = w.get("word", w.get("text", ""))
            tag = _anim_tag(s["animation"], word_counter)
            word_counter += 1
            sty = f"Speaker{si}H" if s["highlight_words"] else f"Speaker{si}"
            lines.append(f"Dialogue: 0,{_fmt_time(ls)},{_fmt_time(le)},{sty},,0,0,0,,{tag}{txt.strip()}")

    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return p


def render_clip(video_path: Path, job_id: str, clip: dict,
                transcript: dict, style: dict, clip_index: int = 0,
                face_data=None, audio_bgm=None,
                color_grade: str = "none", auto_zoom: bool = True) -> Path:
    """Render a single clip with subtitles, auto-zoom, and color grading."""
    output_dir = OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"clip_{clip_index:02d}.mp4"

    clip_dur = clip["end"] - clip["start"]
    start_time = max(0, clip["start"] - 0.5)
    clip_duration = clip_dur + 1.0

    ratio = style.get("aspect_ratio", "9:16")
    w, h = ASPECT_RATIOS.get(ratio, (1080, 1920))
    codec_cfg = VIDEO_CODECS.get(style.get("video_codec", "h264"), VIDEO_CODECS["h264"])

    # Build ASS subtitle
    ass_path = _build_ass(transcript, clip, style, job_id, clip_index, face_data, w, h)
    ass_rel = _rel_path(ass_path)
    video_rel = _rel_path(video_path)
    output_rel = _rel_path(output_path)

    # Video filter chain
    vf_parts = [
        f"ass='{ass_rel}'",
        f"scale={w}:{h}:force_original_aspect_ratio=increase",
        f"crop={w}:{h}",
    ]

    # Auto-zoom (Ken Burns)
    if auto_zoom and clip_dur > 3:
        zoom_pct = random.uniform(1.02, 1.08)
        vf_parts.append(
            f"zoompan=z='min(zoom+0.0015,{zoom_pct})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}")

    # Color grading
    color_filters = {
        "warm": "eq=saturation=1.2:brightness=0.02",
        "cool": "eq=saturation=0.9:brightness=-0.02",
        "vibrant": "eq=saturation=1.4:contrast=1.1:brightness=0.03",
        "cinematic": "eq=saturation=0.85:contrast=1.15:brightness=-0.05",
        "none": "",
    }
    if color_grade in color_filters and color_filters[color_grade]:
        vf_parts.append(color_filters[color_grade])

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg", "-ss", str(start_time), "-i", video_rel,
        "-t", str(clip_duration), "-vf", vf,
        "-c:v", codec_cfg["codec"], "-preset", codec_cfg["preset"],
        "-crf", codec_cfg["crf"],
        "-c:a", "aac", "-b:a", "192k", "-y", output_rel,
    ]

    log.info(f"[Render] Clip {clip_index}: {clip_dur:.1f}s, {style.get('subtitle_style','?')}")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=RENDER_TIMEOUT, cwd=_to_unix(Path.cwd()))
    if r.returncode != 0:
        err = r.stderr[-800:] if len(r.stderr) > 800 else r.stderr
        raise RuntimeError(f"FFmpeg error: {err}")
    log.info(f"[Render] Clip {clip_index} OK: {output_path.name}")
    return output_path

# ===== AUDIO PROCESSING =====

def mix_background_music(video_path: Path, bgm_path: Path,
                         output_path: Path, volume_db: float = -18.0,
                         fade_in: float = 2.0, fade_out: float = 3.0) -> Path:
    """Mix background music into video."""
    cmd = [
        "ffmpeg", "-i", _rel_path(video_path), "-i", _rel_path(bgm_path),
        "-filter_complex",
        f"[1:a]volume={volume_db}dB,afade=t=in:d={fade_in},"
        f"afade=t=out:st={fade_in}:d={fade_out}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-y", _rel_path(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                       cwd=_to_unix(Path.cwd()))
    if r.returncode != 0:
        raise RuntimeError(f"BGM mix error: {r.stderr[-500:]}")
    return output_path

def normalize_audio(video_path: Path, output_path: Path,
                    target_db: float = -16.0) -> Path:
    """Normalize audio loudness."""
    cmd = [
        "ffmpeg", "-i", _rel_path(video_path),
        "-af", f"loudnorm=I={target_db}:TP=-1.5:LRA=11",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-y", _rel_path(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                       cwd=_to_unix(Path.cwd()))
    if r.returncode != 0:
        raise RuntimeError(f"Audio normalize error: {r.stderr[-500:]}")
    return output_path

# ===== FINAL: CONCATENATE =====

def concatenate_clips(job_id: str, clip_paths: list) -> Path:
    """Concatenate multiple clips into final video."""
    output_dir = OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / f"{job_id}_final.mp4"

    cf = output_dir / "concat.txt"
    with open(cf, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{_rel_path(cp)}'\n")

    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", _rel_path(cf), "-c", "copy", "-y", _rel_path(final),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                       cwd=_to_unix(Path.cwd()))
    if r.returncode != 0:
        err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
        raise RuntimeError(f"Concat error: {err}")
    log.info(f"[Concat] Final: {final}")
    return final

# ===== PIPELINE ORCHESTRATOR =====

def run_full_pipeline(url: str, job_id: str, **kwargs) -> Dict:
    """Run complete pipeline: download -> transcribe -> analyze -> render.

    Args:
        url: YouTube URL
        job_id: Unique job identifier
        **kwargs: See GenerateRequest model for options

    Returns:
        Dict with job results including output_paths
    """
    target_duration = kwargs.get("target_duration", 60)
    face_tracking = kwargs.get("face_tracking", True)
    diarization = kwargs.get("diarization", True)
    language = kwargs.get("language", None)
    clip_count = kwargs.get("clip_count", 3)
    color_grade = kwargs.get("color_grade", "none")
    auto_zoom = kwargs.get("auto_zoom", True)

    result = {
        "job_id": job_id,
        "status": "processing",
        "stages": {},
    }

    # Stage 1: Download
    log.info(f"[Pipeline] Stage 1/5: Downloading...")
    video_path = _retry(download_youtube, url, job_id)
    result["stages"]["download"] = {"status": "ok", "path": str(video_path)}

    # Stage 2: Face tracking
    face_data = None
    if face_tracking:
        log.info(f"[Pipeline] Stage 2/5: Face tracking...")
        try:
            face_data = _retry(analyze_faces, video_path, job_id)
            result["stages"]["face_tracking"] = {"status": "ok", "samples": len(face_data)}
        except Exception as e:
            log.warning(f"[Pipeline] Face tracking failed (non-fatal): {e}")
            result["stages"]["face_tracking"] = {"status": "skipped", "error": str(e)}

    # Stage 3: Transcribe
    log.info(f"[Pipeline] Stage 3/5: Transcribing...")
    transcript = _retry(transcribe_video, video_path, job_id, language, diarization)
    result["stages"]["transcribe"] = {
        "status": "ok",
        "language": transcript.get("language", "?"),
        "segments": len(transcript.get("segments", [])),
    }

    # Stage 4: Analyze
    log.info(f"[Pipeline] Stage 4/5: Analyzing...")
    clips = analyze_content(transcript, target_duration, face_data, clip_count)
    if not clips:
        raise RuntimeError("No clips found. Try shorter target_duration or longer video.")
    result["stages"]["analyze"] = {"status": "ok", "clips_found": len(clips)}

    # Stage 5: Render
    log.info(f"[Pipeline] Stage 5/5: Rendering {len(clips)} clips...")
    rendered = []
    for i, clip in enumerate(clips):
        cp = _retry(
            render_clip, video_path, job_id, clip, transcript,
            kwargs, i, face_data, None, color_grade, auto_zoom)
        rendered.append(cp)

    if not rendered:
        raise RuntimeError("All renders failed.")

    final = rendered[0]
    if len(rendered) > 1:
        final = concatenate_clips(job_id, rendered)

    result["status"] = "completed"
    result["output_path"] = str(final)
    result["clips"] = [str(r) for r in rendered]
    result["stages"]["render"] = {"status": "ok", "clips": len(rendered)}

    log.info(f"[Pipeline] COMPLETE: {final}")
    return result
