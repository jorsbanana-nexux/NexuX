"""AGENT_04_CONTENT_PLANNER - Video Architecture Designer"""

from typing import Dict, List, Any
from utils.logger import get_logger

log = get_logger("agent_04")

class ContentPlanner:
    """Agent 04: Builds structural blueprint for high-retention videos."""

    async def create_structure(self, topic, target_duration=60, style="casual"):
        log.info(f"Planning structure: {topic[:50]} ({target_duration}s)")
        d = target_duration
        segments = [
            {"name": "hook", "start": 0, "end": max(3, int(d*0.05)),
             "purpose": "Immediate visual+audio pattern interrupt"},
            {"name": "setup", "start": max(3, int(d*0.05)), "end": int(d*0.25),
             "purpose": "Establish context and curiosity gap"},
            {"name": "buildup", "start": int(d*0.25), "end": int(d*0.55),
             "purpose": "Raise stakes, layer tension"},
            {"name": "climax", "start": int(d*0.55), "end": int(d*0.85),
             "purpose": "Deliver the main revelation/twist"},
            {"name": "resolution", "start": int(d*0.85), "end": int(d*0.95),
             "purpose": "Satisfying conclusion"},
            {"name": "cta", "start": int(d*0.95), "end": d,
             "purpose": "Follow/like/comment trigger"},
        ]
        for i in range(len(segments)-1):
            segments[i]["end"] = segments[i+1]["start"]
        segments[-1]["end"] = d

        retention_anchors = []
        interval = max(5, d//8)
        for t in range(2, d, interval):
            retention_anchors.append({"timestamp": t, "type": "text_pop" if t<15 else "visual_change",
                                       "intensity": min(100, 30+(t//interval)*10)})
        log.success(f"Structure: {len(segments)} segments, {d}s")
        return {"topic": topic, "target_duration": d, "style": style,
                "segments": segments, "retention_anchors": retention_anchors}

content_planner = ContentPlanner()
