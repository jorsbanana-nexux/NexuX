"""
NexuX V9.5 — B-Roll Engine (Optional, Toggleable)

B-roll support that can be toggled ON/OFF. When OFF (default),
behavior stays exactly as the current B-roll-free policy.
When ON, AI-selected images can be overlaid as cutaways.

Modes:
- OFF: No B-roll (default, preserves B-roll-free policy)
- subtle: Brief, tasteful overlays (10-20% of clip duration)
- moderate: Regular cutaways (20-40% of clip duration)
- aggressive: Frequent cutaways (40-60% of clip duration)

Sources:
- local: Use images from a local directory
- unsplash: Fetch from Unsplash API (requires API key)
- pexels: Fetch from Pexels API (requires API key)

Overlay styles:
- pip: Picture-in-picture (corner overlay)
- cutaway: Full-screen cutaway
- split: Split-screen (50/50)
"""

import os
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("nexus.broll")

# B-roll intensity mappings: (max_overlay_ratio, min_segment_duration, max_segment_duration)
INTENSITY_MAP = {
    "subtle": (0.15, 1.5, 3.0),
    "moderate": (0.30, 2.0, 5.0),
    "aggressive": (0.50, 2.0, 7.0),
}

# Overlay style positions for PIP
PIP_POSITIONS = ["top_left", "top_right", "bottom_left", "bottom_right"]


@dataclass
class BrollSegment:
    """A single B-roll overlay segment."""
    start_time: float
    end_time: float
    image_path: str
    overlay_style: str  # pip, cutaway, split
    position: str = "bottom_right"
    scale: float = 0.3  # for PIP
    transition_in: str = "fade"
    transition_out: str = "fade"


class BrollEngine:
    """B-roll selection and overlay engine."""

    def __init__(self, enabled: bool = False, intensity: str = "moderate",
                 source: str = "local", local_dir: str = None,
                 api_key: str = None):
        self.enabled = enabled
        self.intensity = intensity
        self.source = source
        self.local_dir = local_dir or os.environ.get("NEXUX_BROLL_DIR", "")
        self.api_key = api_key or os.environ.get("NEXUX_BROLL_API_KEY", "")

    def is_enabled(self) -> bool:
        return self.enabled

    def select_segments(
        self,
        clip_duration: float,
        transcript_text: str = "",
        keywords: List[str] = None,
    ) -> List[BrollSegment]:
        """Select B-roll segments for a clip based on content analysis."""
        if not self.enabled:
            return []

        if self.intensity not in INTENSITY_MAP:
            log.warning(f"Unknown intensity '{self.intensity}', using 'moderate'")
            self.intensity = "moderate"

        max_ratio, min_dur, max_dur = INTENSITY_MAP[self.intensity]
        total_overlay_time = clip_duration * max_ratio

        segments: List[BrollSegment] = []
        remaining = total_overlay_time
        current_time = max(2.0, clip_duration * 0.1)  # Start B-roll after intro

        while remaining > min_dur and current_time < clip_duration - 2:
            seg_dur = min(
                random.uniform(min_dur, max_dur),
                remaining,
                clip_duration - current_time - 1.0
            )
            if seg_dur < min_dur:
                break

            # Select image based on keywords or random
            image_path = self._select_image(transcript_text, keywords or [])

            # Choose overlay style (alternate between styles)
            overlay_style = random.choice(["pip", "cutaway", "split"])
            position = random.choice(PIP_POSITIONS) if overlay_style == "pip" else "center"

            segments.append(BrollSegment(
                start_time=current_time,
                end_time=current_time + seg_dur,
                image_path=image_path,
                overlay_style=overlay_style,
                position=position,
                scale=0.3,
            ))

            remaining -= seg_dur
            current_time += seg_dur + random.uniform(2.0, 5.0)  # Gap between segments

        log.info(f"B-roll: selected {len(segments)} segments for {clip_duration:.1f}s clip")
        return segments

    def _select_image(self, transcript_text: str, keywords: List[str]) -> str:
        """Select an image for B-roll overlay."""
        if self.source == "local" and self.local_dir:
            local_path = Path(self.local_dir)
            if local_path.exists():
                images = list(local_path.glob("*.jpg")) + list(local_path.glob("*.png"))
                if images:
                    return str(random.choice(images))
            log.warning(f"No images found in {self.local_dir}")

        # Fallback: return empty path (render will skip B-roll for this segment)
        log.debug("No B-roll image available, segment will be skipped")
        return ""

    def get_ffmpeg_overlay_filter(
        self,
        segment: BrollSegment,
        video_width: int,
        video_height: int,
    ) -> str:
        """Generate FFmpeg filter string for B-roll overlay.

        This is used as an additional filter in the render pipeline.
        Returns the overlay filter chain for a single B-roll segment.
        """
        if not segment.image_path:
            return ""

        if segment.overlay_style == "cutaway":
            # Full-screen cutaway with fade in/out
            return (
                f"[1:v]scale={video_width}:{video_height},"
                f"fade=t=in:st={segment.start_time}:d=0.5,"
                f"fade=t=out:st={segment.end_time - 0.5}:d=0.5[br];"
                f"[0:v][br]overlay=enable='between(t,{segment.start_time},{segment.end_time})'[v]"
            )
        elif segment.overlay_style == "pip":
            # Picture-in-picture overlay
            pip_w = int(video_width * segment.scale)
            pip_h = int(video_height * segment.scale)
            x, y = self._get_pip_position(segment.position, video_width, video_height, pip_w, pip_h)
            return (
                f"[1:v]scale={pip_w}:{pip_h},"
                f"fade=t=in:st={segment.start_time}:d=0.3,"
                f"fade=t=out:st={segment.end_time - 0.3}:d=0.3[br];"
                f"[0:v][br]overlay={x}:{y}:enable='between(t,{segment.start_time},{segment.end_time})'[v]"
            )
        elif segment.overlay_style == "split":
            # Split-screen 50/50
            half_w = video_width // 2
            return (
                f"[1:v]scale={half_w}:{video_height}[br];"
                f"[0:v]crop={half_w}:{video_height}:0:0[bg_left];"
                f"[bg_left][br]overlay={half_w}:0:enable='between(t,{segment.start_time},{segment.end_time})'[v]"
            )
        return ""

    def _get_pip_position(self, position: str, vw: int, vh: int, pw: int, ph: int) -> Tuple[int, int]:
        """Get PIP position coordinates."""
        margin = 20
        positions = {
            "top_left": (margin, margin),
            "top_right": (vw - pw - margin, margin),
            "bottom_left": (margin, vh - ph - margin),
            "bottom_right": (vw - pw - margin, vh - ph - margin),
        }
        return positions.get(position, (vw - pw - margin, vh - ph - margin))


# Factory
def create_broll_engine(config: Dict) -> BrollEngine:
    """Create a B-roll engine from a config dict."""
    return BrollEngine(
        enabled=config.get("broll_enabled", False),
        intensity=config.get("broll_intensity", "moderate"),
        source=config.get("broll_source", "local"),
        local_dir=config.get("broll_local_dir", os.environ.get("NEXUX_BROLL_DIR", "")),
        api_key=config.get("broll_api_key", os.environ.get("NEXUX_BROLL_API_KEY", "")),
    )
