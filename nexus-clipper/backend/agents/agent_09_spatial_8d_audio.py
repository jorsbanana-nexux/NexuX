"""AGENT_09_SPATIAL_8D_AUDIO - panning effect analyzer.

Maps detected speakers to stereo pan positions so the downstream renderer
can place each voice in the stereo field (a lightweight "8D" spatial effect).
This agent only *analyzes* and *plans* — it never modifies audio files and
never fabricates success.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger

log = get_logger("agent_09")


class Spatial8DAudio:
    """Maps speakers to stereo pan positions for spatial/8D panning analysis."""

    # Supported panning patterns.
    PATTERNS = ("circular", "linear", "alternating", "centered")

    async def apply_spatial_effect(self, audio_path, pattern="circular", intensity=0.5):
        log.info("Spatial 8D audio analysis only — no audio is modified")
        return {
            "success": False,
            "supported": False,
            "output_path": audio_path,
            "note": "Spatial 8D audio does not modify audio. Use process() to obtain a speaker→pan plan.",
        }

    async def generate_psychoacoustic_pulse(self, duration_s=60, frequency_hz=40):
        return {
            "success": False,
            "supported": False,
            "note": "Psychoacoustic pulse generation is not implemented.",
        }

    # ------------------------------------------------------------------ #
    # Core analysis: map speakers to stereo positions.
    # ------------------------------------------------------------------ #
    async def process(
        self,
        speech_segments: List[Dict[str, Any]],
        pattern: str = "circular",
        intensity: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Analyze a panning effect and map speakers to stereo positions.

        Args:
            speech_segments: list of dicts, each carrying at least a ``speaker``
                key (and optionally ``start`` / ``end`` times in seconds). If the
                list is empty, an empty mapping is returned.
            pattern: panning layout — one of ``circular``, ``linear``,
                ``alternating``, ``centered``.
            intensity: 0.0–1.0 strength of the panning effect (1.0 = full
                hard-left/hard-right spread, 0.0 = mono center).

        Returns:
            Dict with ``status``, ``agent``, and ``spatial_mapping`` — a dict
            of ``speaker -> {pan, left_gain, right_gain, angle_degrees}``.
        """
        # ---- normalise inputs ------------------------------------------- #
        if pattern not in self.PATTERNS:
            log.warning("Unknown pattern %r — falling back to 'circular'", pattern)
            pattern = "circular"

        intensity = max(0.0, min(1.0, float(intensity)))

        if not speech_segments:
            return {
                "status": "completed",
                "agent": "agent_09_spatial_8d_audio",
                "pattern": pattern,
                "intensity": intensity,
                "spatial_mapping": {},
                "note": "No speech segments supplied; empty spatial mapping.",
            }

        # Collect ordered unique speakers (preserve first-seen order).
        speakers: List[str] = []
        seen = set()
        for seg in speech_segments:
            spk = seg.get("speaker") or seg.get("speaker_id") or "speaker"
            if spk not in seen:
                seen.add(spk)
                speakers.append(str(spk))

        # ---- compute pan positions -------------------------------------- #
        pan_positions = self._assign_pans(speakers, pattern, intensity)

        spatial_mapping: Dict[str, Dict[str, float]] = {}
        for spk, (pan, angle_deg) in pan_positions.items():
            left_gain, right_gain = self._equal_power_gains(pan)
            spatial_mapping[spk] = {
                "pan": round(pan, 4),
                "left_gain": round(left_gain, 4),
                "right_gain": round(right_gain, 4),
                "angle_degrees": round(angle_deg, 2),
            }

        log.info(
            "Spatial mapping for %d speaker(s) via '%s' (intensity=%.2f)",
            len(speakers), pattern, intensity,
        )

        return {
            "status": "completed",
            "agent": "agent_09_spatial_8d_audio",
            "pattern": pattern,
            "intensity": intensity,
            "speaker_count": len(speakers),
            "spatial_mapping": spatial_mapping,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _assign_pans(
        self, speakers: List[str], pattern: str, intensity: float
    ) -> Dict[str, Tuple[float, float]]:
        """Return ``speaker -> (pan, angle_degrees)`` for the given pattern."""
        n = len(speakers)
        out: Dict[str, Tuple[float, float]] = {}

        if n == 1:
            out[speakers[0]] = (0.0, 0.0)
            return out

        if pattern == "circular":
            # Distribute speakers evenly around the listener (0°..360°).
            # Pan = sin(angle); intensity scales the spread.
            for i, spk in enumerate(speakers):
                angle = (i / n) * 2.0 * math.pi
                pan = math.sin(angle) * intensity
                out[spk] = (pan, math.degrees(angle))

        elif pattern == "linear":
            # Evenly spread from hard-left to hard-right.
            for i, spk in enumerate(speakers):
                t = i / (n - 1)
                pan = (t * 2.0 - 1.0) * intensity
                angle = (t - 0.5) * 180.0
                out[spk] = (pan, angle)

        elif pattern == "alternating":
            # Bounce left/right/center between successive speakers.
            cycle = (-1.0, 1.0, 0.0)
            for i, spk in enumerate(speakers):
                pan = cycle[i % 3] * intensity
                angle = pan * 90.0
                out[spk] = (pan, angle)

        elif pattern == "centered":
            # Keep main speaker centered, pan others gently outward.
            for i, spk in enumerate(speakers):
                if i == 0:
                    out[spk] = (0.0, 0.0)
                else:
                    side = 1 if (i % 2) else -1
                    pan = side * (i / n) * intensity
                    out[spk] = (pan, pan * 90.0)
        return out

    @staticmethod
    def _equal_power_gains(pan: float) -> Tuple[float, float]:
        """
        Convert a pan value (-1..1) into (left_gain, right_gain) using the
        equal-power (constant-power) panning law.
        """
        # Map pan [-1, 1] to an angle [0, π/2].
        angle = (pan + 1.0) / 2.0 * (math.pi / 2.0)
        left = math.cos(angle)
        right = math.sin(angle)
        return left, right


spatial_8d_audio = Spatial8DAudio()
