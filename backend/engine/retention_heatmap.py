r"""
NexuX V9.6 — Retention Heatmap Engine
======================================
Second-by-second retention prediction for a clip — the analytics layer
Opus Clip shows as a single black-box number, exposed here as a full
transparent curve with per-second reasoning.

Model:
- Baseline exponential decay calibrated by hook strength: a strong hook
  lengthens tau (viewers commit early), a weak hook collapses the curve.
- Local modifiers per second:
  - speech density (words/second in a ±1.5s window) rewards the curve
  - silent seconds (no overlapping speech) apply a penalty — dead air kills
  - emotional/viral keyword hits give a small bump
- The curve is smoothed and clamped monotonic-with-tolerance so local bumps
  read as "retention spikes", not noise.

Output feeds the editor heatmap overlay and the clip-ranking API.
"""
import logging
import math
import re
from typing import Dict, List, Optional

log = logging.getLogger("nexus.retention")

# High-arousal keywords (EN + ID) that measurably spike short-form retention
_SPIKE_WORDS = re.compile(
    r"\b(secret|shocking|never|always|truth|mistake|warning|stop|free|"
    r"rahasia|terbongkar|jangan|ternyata|kesalahan|gratis|bahaya)\b",
    re.IGNORECASE,
)

_BASE_TAU = 22.0       # seconds — decay constant for an average clip
_HOOK_TAU_BONUS = 26.0 # extra tau for a perfect hook (score 1.0)
_SILENCE_PENALTY = 7.0 # points per silent second
_DENSITY_MAX_BOOST = 5.0
_SPIKE_BOOST = 2.5


def _speech_density(t: float, events: List[Dict], window: float = 1.5) -> float:
    """Estimated words-per-second spoken around time t.

    Events may be word-level (1 word) or segment-level (N words) — we weight
    by the fraction of each event overlapping the window so both transcript
    granularities yield comparable densities.
    """
    lo, hi = t - window, t + window
    words = 0.0
    for e in events:
        if e["end"] <= lo or e["start"] >= hi:
            continue
        dur = e["end"] - e["start"]
        if dur <= 0:
            continue
        overlap = min(e["end"], hi) - max(e["start"], lo)
        n_words = max(1, len(e["text"].split()))
        words += n_words * (overlap / dur)
    return words / (2 * window)


def _word_events(transcript: Dict) -> List[Dict]:
    """Flatten transcript into word/segment events with start/end."""
    events = []
    for seg in transcript.get("segments", []) or []:
        words = seg.get("words") or []
        if words:
            for w in words:
                try:
                    ws, we = float(w.get("start", 0)), float(w.get("end", 0))
                except (TypeError, ValueError):
                    continue
                if we > ws:
                    events.append({"start": ws, "end": we,
                                   "text": str(w.get("word", w.get("text", "")))})
        else:
            try:
                ss, se = float(seg.get("start", 0)), float(seg.get("end", 0))
            except (TypeError, ValueError):
                continue
            if se > ss:
                events.append({"start": ss, "end": se,
                               "text": str(seg.get("text", ""))})
    events.sort(key=lambda e: e["start"])
    return events


def predict_retention_curve(
    clip: Dict,
    transcript: Dict,
    hook_strength: float = 0.5,
    resolution: float = 1.0,
) -> Dict:
    """Predict per-second audience retention for a clip.

    Args:
        clip: {"start": float, "end": float} absolute window.
        transcript: transcript dict (word or segment level).
        hook_strength: 0.0-1.0 hook quality (e.g. from hook_detection score/100).
        resolution: seconds per curve point (default 1.0).

    Returns:
        {
          curve: [{t, retention, speech_rate, silent, spike}],
          avg_retention, final_retention, grade,
          dropoff_points: [{t, drop, reason}],
          strongest_window: {t_start, t_end, retention},
        }
    """
    try:
        cs, ce = float(clip.get("start", 0)), float(clip.get("end", 0))
    except (TypeError, ValueError):
        cs, ce = 0.0, 0.0
    duration = max(0.0, ce - cs)
    if duration <= 0:
        return {
            "curve": [], "avg_retention": 0.0, "final_retention": 0.0,
            "grade": "D", "dropoff_points": [], "strongest_window": None,
        }

    hook_strength = max(0.0, min(1.0, hook_strength))
    tau = _BASE_TAU + _HOOK_TAU_BONUS * hook_strength
    events = _word_events(transcript)

    curve: List[Dict] = []
    resolution = max(0.25, resolution)
    n = int(duration / resolution) + 1

    prev = 100.0
    for i in range(n):
        t_rel = min(duration, i * resolution)
        t_abs = cs + t_rel

        base = 100.0 * math.exp(-t_rel / tau)
        density = _speech_density(t_abs, events)
        silent = density < 0.05
        spike = False

        value = base
        if silent:
            value -= _SILENCE_PENALTY * (1 - math.exp(-t_rel / tau))
        else:
            value += min(_DENSITY_MAX_BOOST, density * 1.2)

        # Keyword spike in a narrow window around t
        for e in events:
            if e["start"] <= t_abs + 0.5 and e["end"] >= t_abs - 0.5:
                if _SPIKE_WORDS.search(e["text"]):
                    spike = True
                    break
        if spike:
            value += _SPIKE_BOOST

        # Allow small upward bumps (spikes) but keep the curve plausible:
        # smoothed toward previous value, hard clamp to [3, 100]
        smoothed = 0.65 * prev + 0.35 * value
        if smoothed > prev:
            smoothed = min(prev + 1.5, smoothed)  # spike ceiling per step
        smoothed = max(3.0, min(100.0, smoothed))

        curve.append({
            "t": round(t_rel, 2),
            "retention": round(smoothed, 1),
            "speech_rate": round(density, 2),
            "silent": silent,
            "spike": spike,
        })
        prev = smoothed

    values = [p["retention"] for p in curve]
    avg = sum(values) / len(values) if values else 0.0
    final = values[-1] if values else 0.0

    # Drop-off points: steep single-step falls, labelled with a reason
    dropoffs = []
    for i in range(1, len(curve)):
        drop = curve[i - 1]["retention"] - curve[i]["retention"]
        if drop >= 2.5:
            reason = "silence" if curve[i]["silent"] else (
                "low_density" if curve[i]["speech_rate"] < 0.3 else "natural_decay")
            dropoffs.append({
                "t": curve[i]["t"], "drop": round(drop, 1), "reason": reason,
            })
    dropoffs.sort(key=lambda d: -d["drop"])

    # Strongest 5-second window (for editor "peak moment" marker)
    strongest = None
    if len(values) >= 5:
        best_i = max(range(len(values) - 4), key=lambda i: sum(values[i:i + 5]))
        strongest = {
            "t_start": curve[best_i]["t"],
            "t_end": curve[min(best_i + 4, len(curve) - 1)]["t"],
            "retention": round(sum(values[best_i:best_i + 5]) / 5, 1),
        }

    grade = ("S" if avg >= 70 else "A" if avg >= 55 else
             "B" if avg >= 40 else "C" if avg >= 28 else "D")

    return {
        "curve": curve,
        "avg_retention": round(avg, 1),
        "final_retention": round(final, 1),
        "grade": grade,
        "dropoff_points": dropoffs[:5],
        "strongest_window": strongest,
        "hook_strength": round(hook_strength, 2),
        "duration": round(duration, 1),
    }
