"""
NexuX V8.0 — Creative Brain
=============================
The "thinking" layer that makes creative decisions like a human editor.

Every time the pipeline runs, the Creative Brain:
1. Analyzes the content tone, pace, and emotion
2. Picks a unique editing style from a rotating creative palette
3. Decides transitions, zoom patterns, subtitle style, color grade
4. Generates creative variations so no two outputs look the same
5. Learns from past successes (feedback memory)

This is what makes NexuX feel alive — not a rigid machine.
"""
import random
import time
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from logging import getLogger

from .constants import OUTPUT_DIR

log = getLogger("nexus.creative")


# ── Creative Style Palette (rotates daily + per-video) ──

CREATIVE_PALETTES = {
    "cinematic_drama": {
        "color_grade": "cinematic",
        "subtitle_style": "cinematic",
        "transition": "dissolve",
        "zoom_style": "slow_push",
        "speed_ramp": True,
        "audio_duck": True,
        "mood": "dramatic",
    },
    "viral_explosive": {
        "color_grade": "vibrant",
        "subtitle_style": "hormozi",
        "transition": "zoom_in",
        "zoom_style": "punch",
        "speed_ramp": True,
        "audio_duck": False,
        "mood": "energetic",
    },
    "clean_minimal": {
        "color_grade": "none",
        "subtitle_style": "minimal",
        "transition": "hard_cut",
        "zoom_style": "subtle",
        "speed_ramp": False,
        "audio_duck": False,
        "mood": "calm",
    },
    "warm_storyteller": {
        "color_grade": "warm",
        "subtitle_style": "storyteller",
        "transition": "fade",
        "zoom_style": "ken_burns",
        "speed_ramp": False,
        "audio_duck": True,
        "mood": "narrative",
    },
    "bold_pop": {
        "color_grade": "hdr_pop",
        "subtitle_style": "karaoke",
        "transition": "zoom_in",
        "zoom_style": "punch",
        "speed_ramp": True,
        "audio_duck": False,
        "mood": "playful",
    },
    "noir_intensity": {
        "color_grade": "noir",
        "subtitle_style": "bold",
        "transition": "fade",
        "zoom_style": "slow_push",
        "speed_ramp": False,
        "audio_duck": True,
        "mood": "intense",
    },
    "vintage_retro": {
        "color_grade": "vintage",
        "subtitle_style": "retro",
        "transition": "dissolve",
        "zoom_style": "ken_burns",
        "speed_ramp": False,
        "audio_duck": True,
        "mood": "nostalgic",
    },
    "tech_futuristic": {
        "color_grade": "cool",
        "subtitle_style": "cyber",
        "transition": "glitch",
        "zoom_style": "punch",
        "speed_ramp": True,
        "audio_duck": False,
        "mood": "futuristic",
    },
}

# ── Transition FFmpeg implementations ──

TRANSITION_FILTERS = {
    "hard_cut": "",  # No filter needed
    "fade": "fade=t=in:st=0:d=0.3,fade=t=out:st={dur}-0.3:d=0.3",
    "dissolve": "fade=t=in:st=0:d=0.5:alpha=1,fade=t=out:st={dur}-0.5:d=0.5:alpha=1",
    "zoom_in": "scale={w}*{t}:ih*{t}:-1:flags=lancoz,crop=iw:ih:((iw-{w})/2):((ih-{h})/2",
    "slide_up": "crop=iw:ih:0:((ih-ih*{t})):0",
    "glitch": "noise=alls=20:allf=t+0.1,hue=h={t}*360",
    "wipe_left": "crop=iw*{t}:ih:0:0",
}


# ── Zoom Styles (different Ken Burns patterns) ──

ZOOM_STYLES = {
    "slow_push": lambda dur, w, h: (
        f"zoompan=z='min(zoom+0.0008,1.15)':d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
    "punch": lambda dur, w, h: (
        f"zoompan=z='if(lt(on,15),1+on*0.02,1.3-(on-15)*0.005)':d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
    "subtle": lambda dur, w, h: (
        f"zoompan=z='1+0.0003*on':d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
    "ken_burns": lambda dur, w, h: (
        f"zoompan=z='1+0.001*sin(on/30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
    "oscillate": lambda dur, w, h: (
        f"zoompan=z='1+0.005*sin(on*0.1)':x='iw/2+(iw/4)*sin(on*0.05)':"
        f"y='ih/2-(ih/zoom/2)':d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
    "breath": lambda dur, w, h: (
        f"zoompan=z='1+0.002*sin(on*PI/75)':d={int(dur*30)}:s={w}x{h}:fps=30"
    ),
}


# ── Creative Memory (learns from past runs) ──

MEMORY_FILE = OUTPUT_DIR / "creative_memory.json"


def _load_memory() -> Dict:
    """Load creative memory from past runs."""
    try:
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "run_count": 0,
        "palette_usage": {},  # which palettes were used
        "palette_scores": {},  # average critic score per palette
        "last_palette": None,
        "successful_patterns": [],
        "failed_patterns": [],
    }


def _save_memory(mem: Dict):
    """Save creative memory."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except Exception as e:
        log.warning(f"[Creative] Memory save failed: {e}")


def _daily_seed() -> int:
    """Generate a seed that changes daily but is consistent within a day."""
    today = time.strftime("%Y-%m-%d")
    return int(hashlib.md5(today.encode()).hexdigest(), 16) % (2**32)


def choose_creative_palette(
    transcript: Dict,
    clips: List[Dict],
    user_overrides: Optional[Dict] = None,
) -> Dict:
    """Choose a creative palette for this run.
    
    The brain considers:
    1. Content tone (from transcript analysis)
    2. Daily rotation (different style each day)
    3. Past success memory (what worked before)
    4. User overrides (if user specified preferences)
    5. Per-video variation (hash of video URL for uniqueness)
    
    Returns a creative config dict with all editing decisions.
    """
    mem = _load_memory()
    
    # Start with user overrides
    if user_overrides:
        palette_name = user_overrides.get("creative_palette")
        if palette_name and palette_name in CREATIVE_PALETTES:
            palette = CREATIVE_PALETTES[palette_name].copy()
            log.info(f"[Creative] User-selected palette: {palette_name}")
        else:
            palette = _auto_choose_palette(transcript, clips, mem, user_overrides)
    else:
        palette = _auto_choose_palette(transcript, clips, mem, user_overrides)
    
    # Apply user overrides on top
    if user_overrides:
        for key in ["color_grade", "subtitle_style", "transition", "zoom_style"]:
            if user_overrides.get(key):
                palette[key] = user_overrides[key]
    
    # Add variation: pick a random zoom sub-style if not specified
    if palette.get("zoom_style") == "random":
        zoom_options = list(ZOOM_STYLES.keys())
        palette["zoom_style"] = random.choice(zoom_options)
    
    # Generate creative decisions per-clip
    clip_decisions = []
    for i, clip in enumerate(clips):
        decision = _decide_clip_creativity(clip, palette, i, len(clips), transcript)
        clip_decisions.append(decision)
    
    # Update memory
    mem["run_count"] += 1
    mem["last_palette"] = palette.get("mood", "unknown")
    palette_name = next(
        (k for k, v in CREATIVE_PALETTES.items() if v.get("mood") == palette.get("mood")),
        "unknown"
    )
    mem["palette_usage"][palette_name] = mem["palette_usage"].get(palette_name, 0) + 1
    _save_memory(mem)
    
    result = {
        "palette": palette,
        "clip_decisions": clip_decisions,
        "memory_run_count": mem["run_count"],
    }
    log.info(f"[Creative] Palette: {palette_name} | Mood: {palette.get('mood')} | "
             f"Zoom: {palette.get('zoom_style')} | Grade: {palette.get('color_grade')}")
    return result


def _auto_choose_palette(
    transcript: Dict,
    clips: List[Dict],
    memory: Dict,
    overrides: Optional[Dict],
) -> Dict:
    """Automatically choose the best palette based on content analysis."""
    
    # Analyze transcript tone
    segments = transcript.get("segments", [])
    all_text = " ".join(s.get("text", "") for s in segments).lower()
    
    # Detect content mood from keywords
    energetic_words = ["amazing", "crazy", "insane", "wow", "incredible", "shocking",
                       "gila", "buset", "edan", "anjir", "viral", "terbongkar"]
    calm_words = ["think", "consider", "reflect", "understand", "learning",
                  "pikir", "renung", "paham", "belajar"]
    dramatic_words = ["but", "however", "suddenly", "changed", "never",
                      "tapi", "namun", "tiba-tiba", "berubah", "tidak pernah"]
    tech_words = ["ai", "technology", "future", "code", "data", "algorithm",
                  "teknologi", "masa depan", "kode", "data", "algoritma"]
    
    energetic_score = sum(1 for w in energetic_words if w in all_text)
    calm_score = sum(1 for w in calm_words if w in all_text)
    dramatic_score = sum(1 for w in dramatic_words if w in all_text)
    tech_score = sum(1 for w in tech_words if w in all_text)
    
    # Calculate speaking pace
    total_duration = 0
    total_words = 0
    for s in segments:
        dur = s.get("end", 0) - s.get("start", 0)
        total_duration += dur
        total_words += len(s.get("text", "").split())
    wps = total_words / max(total_duration, 1) if total_duration > 0 else 2
    
    # Score each palette
    scores = {}
    for name, palette in CREATIVE_PALETTES.items():
        mood = palette.get("mood", "")
        score = 0
        
        if mood == "energetic" and energetic_score > 0:
            score += energetic_score * 3
        if mood == "calm" and calm_score > 0:
            score += calm_score * 3
        if mood == "dramatic" and dramatic_score > 0:
            score += dramatic_score * 2
        if mood == "futuristic" and tech_score > 0:
            score += tech_score * 3
        if mood == "narrative" and calm_score > 0:
            score += calm_score * 2
        if mood == "playful" and wps > 3.5:
            score += 2
        
        # Daily rotation bonus — avoid repeating yesterday's palette
        if name == memory.get("last_palette"):
            score -= 5  # Penalty for repeating
        
        # Usage penalty — prefer less-used palettes
        usage = memory.get("palette_usage", {}).get(name, 0)
        score -= usage * 0.5
        
        # Add daily seed for variation
        daily = _daily_seed()
        rng = random.Random(daily + hash(name))
        score += rng.uniform(0, 3)
        
        scores[name] = score
    
    # Pick the highest scoring palette
    best_name = max(scores, key=scores.get)
    log.info(f"[Creative] Palette scores: {dict(sorted(scores.items(), key=lambda x: -x[1])[:3])}")
    
    return CREATIVE_PALETTES[best_name].copy()


def _decide_clip_creativity(
    clip: Dict,
    palette: Dict,
    clip_idx: int,
    total_clips: int,
    transcript: Dict,
) -> Dict:
    """Make per-clip creative decisions.
    
    Each clip gets unique treatment while staying cohesive with the palette.
    """
    clip_start = clip.get("start", 0)
    clip_end = clip.get("end", 60)
    clip_dur = clip_end - clip_start
    
    # Find segments in this clip
    segments = transcript.get("segments", [])
    clip_segs = [s for s in segments if s.get("start", 0) < clip_end and s.get("end", 0) > clip_start]
    
    # Speaking pace in this clip
    clip_words = sum(len(s.get("text", "").split()) for s in clip_segs)
    clip_wps = clip_words / max(clip_dur, 1)
    
    decisions = {
        "clip_index": clip_idx,
        "transition": palette.get("transition", "hard_cut"),
        "zoom_style": palette.get("zoom_style", "subtle"),
        "color_grade": palette.get("color_grade", "none"),
        "speed_ramp": palette.get("speed_ramp", False),
        "audio_duck": palette.get("audio_duck", False),
    }
    
    # First clip gets an intro transition
    if clip_idx == 0:
        decisions["transition"] = "fade"
        decisions["is_intro"] = True
    
    # Last clip gets an outro transition
    if clip_idx == total_clips - 1:
        decisions["is_outro"] = True
    
    # High-energy segment → punch zoom
    if clip_wps > 4.0 and palette.get("zoom_style") != "subtle":
        decisions["zoom_style"] = "punch"
    
    # Slow segment → ken burns
    if clip_wps < 2.0:
        decisions["zoom_style"] = "ken_burns"
    
    # Speed ramp for dramatic moments (detected by text analysis)
    if decisions.get("speed_ramp"):
        # Find the most exciting moment in the clip
        best_moment = _find_speed_ramp_moment(clip_segs, clip_start, clip_end)
        if best_moment:
            decisions["speed_ramp_at"] = best_moment
            decisions["speed_ramp_type"] = "dramatic_slowmo"
    
    return decisions


def _find_speed_ramp_moment(
    segments: List[Dict],
    clip_start: float,
    clip_end: float,
) -> Optional[float]:
    """Find the best moment for a speed ramp (dramatic slow-mo)."""
    from .constants import EXCITEMENT_KEYWORDS
    
    best_score = 0
    best_time = None
    
    for seg in segments:
        text = seg.get("text", "").lower()
        score = sum(1 for kw in EXCITEMENT_KEYWORDS if kw in text)
        if score > best_score:
            best_score = score
            best_time = seg.get("start", clip_start)
    
    return best_time


def record_outcome(palette_name: str, avg_score: float, success: bool):
    """Record the outcome of a creative choice for learning."""
    mem = _load_memory()
    
    if success:
        scores = mem.setdefault("palette_scores", {})
        current = scores.get(palette_name, [])
        current.append(avg_score)
        # Keep only last 20 runs
        if len(current) > 20:
            current = current[-20:]
        scores[palette_name] = current
        
        # Record successful pattern
        patterns = mem.setdefault("successful_patterns", [])
        patterns.append({
            "palette": palette_name,
            "score": avg_score,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        })
        if len(patterns) > 50:
            patterns = patterns[-50:]
    else:
        failed = mem.setdefault("failed_patterns", [])
        failed.append({
            "palette": palette_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        })
        if len(failed) > 20:
            failed = failed[-20:]
    
    _save_memory(mem)
    log.info(f"[Creative] Recorded outcome: {palette_name} score={avg_score:.2f} success={success}")


def get_transition_filter(
    transition: str,
    clip_duration: float,
    width: int,
    height: int,
) -> str:
    """Get FFmpeg filter string for a transition."""
    template = TRANSITION_FILTERS.get(transition, "")
    if not template:
        return ""
    return template.format(dur=clip_duration, w=width, h=height)


def get_zoom_filter(
    zoom_style: str,
    clip_duration: float,
    width: int,
    height: int,
) -> str:
    """Get FFmpeg zoompan filter for a zoom style."""
    generator = ZOOM_STYLES.get(zoom_style, ZOOM_STYLES["subtle"])
    return generator(clip_duration, width, height)
