"""AGENT_13_VISUAL_QUALITY_CHECKER - compatibility adapter over Local-First V5 QA."""

from utils.logger import get_logger
from v5_bridge import visual_quality

log = get_logger("agent_13")

class VisualQualityChecker:
    async def check_clip(self, video_path, start_time=0, end_time=None):
        try:
            return visual_quality(video_path, float(start_time or 0.0), None if end_time is None else float(end_time))
        except Exception as exc:
            log.exception("Visual quality check failed")
            return {"passed": False, "score": 0, "issues": [str(exc)]}

    async def scan_for_watermarks(self, video_path):
        return {
            "supported": False,
            "passed": False,
            "watermarks_found": None,
            "note": "Watermark detection is not implemented. NexuX never removes or hides source watermarks.",
        }

visual_quality_checker = VisualQualityChecker()
