"""
NexuX V8.0 — Editorial Critic & Revision Loop
=======================================================
The quality gate that makes NexuX a discerning professional editor.

This module evaluates each rendered clip on multiple quality dimensions,
can REJECT clips that don't meet the gold standard, and provides specific
feedback on how to improve. Unlike Agent 23 (which just said "retry"),
this critic actually analyzes what's wrong and prescribes fixes.

Revision Loop:
1. Evaluate clip on 6 quality dimensions
2. If any dimension falls below threshold → REJECT
3. Generate specific improvement directives
4. Feed directives back to the render/analyze pipeline
5. Re-render with adjusted parameters
6. Re-evaluate (max 3 iterations)
"""
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .editorial import EditorialScore, analyze_editorial

log = logging.getLogger("nexus.critic")


# ── Quality Thresholds ───────────────────────────────

GOLD_STANDARD = {
    "editorial_composite": 0.65,     # Must be a genuinely good clip editorially
    "coherence": 0.50,               # Must stand alone as a thought
    "hook_intelligence": 0.40,       # Must have a real hook
    "narrative_completeness": 0.40,   # Must have some narrative structure
    "emotional_arc": 0.35,            # Must have some emotional movement
    "technical_quality": 0.70,       # FFmpeg render must be clean
}

MINIMUM_ACCEPTABLE = {
    "editorial_composite": 0.40,
    "coherence": 0.35,
    "hook_intelligence": 0.25,
    "narrative_completeness": 0.25,
    "emotional_arc": 0.20,
    "technical_quality": 0.50,
}

MAX_REVISIONS = 3


# ── Data Structures ───────────────────────────────────

@dataclass
class CritiqueResult:
    """Result of critic evaluation of a single clip."""
    clip_index: int
    verdict: str  # "GOLD", "ACCEPTABLE", "NEEDS_REVISION", "REJECT"
    dimensions: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    revision_directives: List[str] = field(default_factory=list)
    revision_count: int = 0
    should_retry: bool = False
    
    @property
    def score(self) -> float:
        return sum(self.dimensions.values()) / max(len(self.dimensions), 1)


# ── Critic Engine ────────────────────────────────────

def evaluate_clip(
    clip: Dict,
    clip_index: int,
    transcript: List[Dict],
    full_duration: float,
    full_segments: List[Dict],
    output_path: Optional[Path] = None,
    revision_count: int = 0,
) -> CritiqueResult:
    """
    Evaluate a clip on multiple quality dimensions.
    
    This is the heart of the critic. It checks both editorial quality
    (is this a good clip?) and technical quality (is the render clean?).
    
    Args:
        clip: Clip candidate dict
        clip_index: Index for logging
        transcript: Full transcript segments
        full_duration: Total video duration
        full_segments: All transcript segments
        output_path: Path to rendered clip (for technical QA)
        revision_count: How many times this clip has been revised
    
    Returns:
        CritiqueResult with verdict and improvement directives
    """
    result = CritiqueResult(clip_index=clip_index, revision_count=revision_count)
    
    # ── Editorial Evaluation ──
    clip_segs = [
        s for s in full_segments
        if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]
    ]
    
    editorial = analyze_editorial(
        clip_segs, clip["start"], clip["end"], full_duration, full_segments
    )
    
    result.dimensions["editorial_composite"] = editorial.composite
    result.dimensions["coherence"] = editorial.coherence
    result.dimensions["hook_intelligence"] = editorial.hook_intelligence
    result.dimensions["narrative_completeness"] = editorial.narrative_completeness
    result.dimensions["emotional_arc"] = editorial.emotional_arc
    
    # ── Technical Quality Evaluation ──
    tech_quality = 1.0  # Assume good unless we find issues
    if output_path and output_path.exists():
        tech_quality = _evaluate_technical_quality(output_path)
    result.dimensions["technical_quality"] = tech_quality
    
    # ── Identify Issues ──
    issues = []
    directives = []
    
    for dim, threshold in GOLD_STANDARD.items():
        val = result.dimensions.get(dim, 0)
        if val < threshold:
            if dim == "hook_intelligence":
                issues.append(f"Weak hook (score: {val:.2f}) — opening doesn't grab attention")
                directives.append("ADJUST_START: Shift clip start to capture a stronger opening line")
            elif dim == "coherence":
                issues.append(f"Low coherence (score: {val:.2f}) — clip feels like a fragment")
                directives.append("EXPAND_BOUNDARIES: Extend clip duration to capture a complete thought")
            elif dim == "narrative_completeness":
                issues.append(f"Incomplete narrative (score: {val:.2f}) — missing setup or payoff")
                directives.append("SEEK_PAYOFF: Adjust clip end to include the conclusion/punchline")
            elif dim == "emotional_arc":
                issues.append(f"Flat emotional arc (score: {val:.2f}) — energy is monotonous")
                directives.append("RETIME: Adjust boundaries to capture emotional shift")
            elif dim == "editorial_composite":
                issues.append(f"Low editorial score (score: {val:.2f}) — clip is not compelling enough")
                directives.append("REPLACE: This clip should be replaced with a higher-scoring candidate")
            elif dim == "technical_quality":
                issues.append(f"Technical quality issues (score: {val:.2f})")
                if tech_quality < 0.5:
                    directives.append("RE_RENDER: Technical issues require re-rendering")
                else:
                    directives.append("TUNE_RENDER: Adjust render parameters for better quality")
    
    result.issues = issues
    result.revision_directives = directives
    
    # ── Verdict ──
    all_gold = all(
        result.dimensions.get(d, 0) >= t
        for d, t in GOLD_STANDARD.items()
    )
    all_acceptable = all(
        result.dimensions.get(d, 0) >= MINIMUM_ACCEPTABLE.get(d, 0)
        for d in MINIMUM_ACCEPTABLE
    )
    
    if all_gold:
        result.verdict = "GOLD"
        log.info(f"[Critic] Clip {clip_index}: GOLD STANDARD ✨ (score: {result.score:.2f})")
    elif all_acceptable:
        result.verdict = "ACCEPTABLE"
        log.info(f"[Critic] Clip {clip_index}: ACCEPTABLE (score: {result.score:.2f})")
    elif revision_count < MAX_REVISIONS and directives:
        result.verdict = "NEEDS_REVISION"
        result.should_retry = True
        log.info(f"[Critic] Clip {clip_index}: NEEDS REVISION (attempt {revision_count + 1}/{MAX_REVISIONS})")
        for issue in issues:
            log.info(f"  ⚠ {issue}")
    else:
        result.verdict = "REJECT"
        log.warning(f"[Critic] Clip {clip_index}: REJECTED after {revision_count} revisions")
        for issue in issues:
            log.warning(f"  ✗ {issue}")
    
    return result


def evaluate_batch(
    clips: List[Dict],
    transcript: Dict,
    output_paths: List[Path],
    full_duration: float,
) -> List[CritiqueResult]:
    """
    Evaluate all clips in a batch.
    
    Returns critique results for each clip, sorted by quality.
    """
    full_segments = transcript.get("segments", [])
    results = []
    
    for i, clip in enumerate(clips):
        out_path = output_paths[i] if i < len(output_paths) else None
        critique = evaluate_clip(
            clip, i, full_segments, full_duration, full_segments, out_path
        )
        results.append(critique)
    
    # Sort by score (best first)
    results.sort(key=lambda r: r.score, reverse=True)
    
    gold = sum(1 for r in results if r.verdict == "GOLD")
    acceptable = sum(1 for r in results if r.verdict == "ACCEPTABLE")
    revise = sum(1 for r in results if r.verdict == "NEEDS_REVISION")
    rejected = sum(1 for r in results if r.verdict == "REJECT")
    
    log.info(f"[Critic] Batch: {gold} GOLD, {acceptable} ACCEPTABLE, "
             f"{revise} NEEDS REVISION, {rejected} REJECTED")
    
    return results


# ── Technical Quality ────────────────────────────────

def _evaluate_technical_quality(output_path: Path) -> float:
    """Evaluate technical quality of a rendered clip using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(output_path)
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if r.returncode != 0:
            log.warning(f"[Critic] ffprobe failed: {r.stderr[:200]}")
            return 0.5  # Can't verify, assume average
        
        data = json.loads(r.stdout)
        score = 1.0
        issues = []
        
        # Check video stream
        video_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            return 0.0
        
        vs = video_streams[0]
        
        # Resolution check
        width = int(vs.get("width", 0))
        height = int(vs.get("height", 0))
        if width < 720 or height < 720:
            score -= 0.2
            issues.append(f"Low resolution: {width}x{height}")
        
        # Duration check
        duration = float(data.get("format", {}).get("duration", 0))
        if duration < 5:
            score -= 0.15
            issues.append(f"Very short clip: {duration:.1f}s")
        
        # Bitrate check
        bitrate = int(data.get("format", {}).get("bit_rate", 0))
        if bitrate > 0 and bitrate < 500_000:
            score -= 0.15
            issues.append(f"Low bitrate: {bitrate / 1000:.0f}kbps")
        
        # Frame rate
        fps_str = vs.get("r_frame_rate", "30/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
            if fps < 24:
                score -= 0.1
                issues.append(f"Low framerate: {fps:.1f}fps")
        except (ValueError, ZeroDivisionError):
            pass
        
        # Check for audio
        audio_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
        if not audio_streams:
            score -= 0.2
            issues.append("No audio stream")
        
        # File is valid and playable
        if score >= 1.0:
            score = 1.0  # Perfect
        
        if issues:
            log.debug(f"[Critic] Technical issues for {output_path.name}: {'; '.join(issues)}")
        
        return max(0.0, min(1.0, score))
        
    except Exception as e:
        log.warning(f"[Critic] Technical evaluation failed: {e}")
        return 0.5


# ── Revision Directives Application ──────────────────

def apply_revision_directives(
    clip: Dict,
    directives: List[str],
    candidates: List[Dict],
    segments: List[Dict],
    full_duration: float,
) -> Optional[Dict]:
    """
    Apply revision directives to produce an improved clip candidate.
    
    This is what makes the critic a REVISION LOOP, not just a pass/fail gate.
    It takes the critic's feedback and produces a new, adjusted clip.
    """
    new_clip = dict(clip)
    changed = False
    
    for directive in directives:
        if directive.startswith("ADJUST_START"):
            # Try to find a better starting point within ±10 seconds
            best_shift = _find_best_start(clip, segments, full_duration)
            if best_shift is not None:
                new_clip["start"] = round(best_shift, 2)
                new_clip["end"] = round(best_shift + (clip["end"] - clip["start"]), 2)
                changed = True
                log.info(f"[Critic] Adjusted start: {clip['start']} → {new_clip['start']}")
        
        elif directive.startswith("EXPAND_BOUNDARIES"):
            # Extend clip to capture more context
            extension = min(5.0, (clip["end"] - clip["start"]) * 0.15)
            new_clip["start"] = max(0, round(clip["start"] - extension, 2))
            new_clip["end"] = min(full_duration, round(clip["end"] + extension, 2))
            changed = True
            log.info(f"[Critic] Expanded boundaries: +{extension:.1f}s total")
        
        elif directive.startswith("SEEK_PAYOFF"):
            # Try to find a payoff/revelation within ±15 seconds of current end
            new_end = _find_payoff(clip, segments, full_duration)
            if new_end is not None and new_end != clip["end"]:
                new_clip["end"] = round(new_end, 2)
                changed = True
                log.info(f"[Critic] Adjusted end for payoff: {clip['end']} → {new_clip['end']}")
        
        elif directive.startswith("RETIME"):
            # Adjust both boundaries to capture emotional shift
            new_bounds = _find_emotional_bounds(clip, segments, full_duration)
            if new_bounds:
                new_clip["start"], new_clip["end"] = new_bounds
                changed = True
                log.info(f"[Critic] Retimed: [{clip['start']}, {clip['end']}] → [{new_clip['start']}, {new_clip['end']}]")
        
        elif directive.startswith("REPLACE"):
            # Find the next best candidate from the pool
            for c in candidates:
                if c.get("editorial", {}).get("verdict") in ("STRONG", "GOOD"):
                    if c["start"] != clip["start"]:
                        new_clip = dict(c)
                        changed = True
                        log.info(f"[Critic] Replaced with higher-scoring candidate")
                        break
        
        elif directive.startswith("RE_RENDER") or directive.startswith("TUNE_RENDER"):
            # These are handled by the render pipeline, not here
            changed = True  # Mark as needing re-render
    
    if not changed:
        return None
    
    return new_clip


def _find_best_start(clip: Dict, segments: List[Dict], full_duration: float) -> Optional[float]:
    """Find the best starting point near the current clip start."""
    from .editorial import _score_hook_intelligence, _get_hook_text
    
    current_start = clip["start"]
    clip_dur = clip["end"] - clip["start"]
    best_score = 0
    best_start = None
    
    # Try shifts from -10 to +10 seconds
    for offset in range(-10, 11, 2):
        candidate_start = max(0, current_start + offset)
        candidate_end = min(full_duration, candidate_start + clip_dur)
        
        clip_segs = [
            s for s in segments
            if s.get("start", 0) < candidate_end and s.get("end", 0) > candidate_start
        ]
        
        hook_text = _get_hook_text(clip_segs, candidate_start, max(3.0, clip_dur * 0.2))
        hook_score = _score_hook_intelligence(hook_text)
        
        if hook_score > best_score + 0.1:
            best_score = hook_score
            best_start = candidate_start
    
    return best_start


def _find_payoff(clip: Dict, segments: List[Dict], full_duration: float) -> Optional[float]:
    """Find a payoff/revelation near the current clip end."""
    from .editorial import _detect_narrative_beats
    
    current_end = clip["end"]
    clip_dur = clip["end"] - clip["start"]
    
    # Search forward for a payoff beat
    for offset in range(0, 16, 2):
        candidate_end = min(full_duration, current_end + offset)
        
        clip_segs = [
            s for s in segments
            if s.get("start", 0) < candidate_end and s.get("end", 0) > clip["start"]
        ]
        
        clip_text = " ".join(s.get("text", "") for s in clip_segs).lower()
        beats = _detect_narrative_beats(clip_text)
        beat_names = [b[0] for b in beats]
        
        if "payoff" in beat_names or "revelation" in beat_names:
            return candidate_end
    
    return None


def _find_emotional_bounds(
    clip: Dict, segments: List[Dict], full_duration: float
) -> Optional[Tuple[float, float]]:
    """Find boundaries that capture an emotional shift."""
    from .editorial import _analyze_emotional_arc
    
    current_start = clip["start"]
    current_end = clip["end"]
    clip_dur = current_end - current_start
    best_score = 0
    best_bounds = None
    
    # Try various boundary combinations
    for start_offset in range(-8, 9, 4):
        for end_offset in range(-4, 9, 4):
            new_start = max(0, current_start + start_offset)
            new_end = min(full_duration, current_end + end_offset)
            
            if new_end - new_start < 10:
                continue
            
            clip_segs = [
                s for s in segments
                if s.get("start", 0) < new_end and s.get("end", 0) > new_start
            ]
            
            arc = _analyze_emotional_arc(clip_segs)
            if arc["score"] > best_score + 0.1:
                best_score = arc["score"]
                best_bounds = (round(new_start, 2), round(new_end, 2))
    
    return best_bounds


# ── Full Revision Loop ────────────────────────────────

def revision_loop(
    clip: Dict,
    clip_index: int,
    candidates: List[Dict],
    transcript: Dict,
    output_path: Optional[Path],
    full_duration: float,
    render_fn=None,
    max_iterations: int = MAX_REVISIONS,
) -> Tuple[Dict, CritiqueResult]:
    """
    Run the full critic revision loop for a single clip.
    
    1. Evaluate
    2. If needs revision → apply directives
    3. Re-render (if render_fn provided)
    4. Re-evaluate
    5. Repeat until GOLD/ACCEPTABLE or max iterations
    
    Returns the final clip and its last critique.
    """
    full_segments = transcript.get("segments", [])
    current_clip = clip
    current_output = output_path
    
    for iteration in range(max_iterations + 1):
        critique = evaluate_clip(
            current_clip, clip_index, full_segments, full_duration,
            full_segments, current_output, iteration
        )
        
        if critique.verdict in ("GOLD", "ACCEPTABLE"):
            log.info(f"[Critic] Clip {clip_index}: {critique.verdict} after {iteration} revisions")
            return current_clip, critique
        
        if not critique.should_retry:
            log.info(f"[Critic] Clip {clip_index}: {critique.verdict} — no more retries")
            return current_clip, critique
        
        # Apply revision directives
        new_clip = apply_revision_directives(
            current_clip, critique.revision_directives,
            candidates, full_segments, full_duration
        )
        
        if new_clip is None:
            log.info(f"[Critic] Clip {clip_index}: No improvement possible")
            return current_clip, critique
        
        current_clip = new_clip
        
        # Re-render if render function provided
        if render_fn and current_output:
            try:
                new_output = render_fn(current_clip, clip_index)
                if new_output:
                    current_output = new_output
            except Exception as e:
                log.warning(f"[Critic] Re-render failed: {e}")
    
    return current_clip, critique
