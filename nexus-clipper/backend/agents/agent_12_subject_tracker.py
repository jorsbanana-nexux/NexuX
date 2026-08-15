"""AGENT_12_SUBJECT_TRACKER - compatibility adapter over Local-First V5 vision."""

from utils.logger import get_logger
from v5_bridge import detect_face_subjects

log = get_logger("agent_12")


class SubjectTracker:
    async def detect_subjects(self, video_path):
        log.info("Detecting real subjects: %s", video_path)
        try:
            observations = detect_face_subjects(video_path, 0.0, None)
            return {
                "success": True,
                "video_path": str(video_path),
                "subject_frames": observations,
                "subject_count": len(observations),
            }
        except Exception as exc:
            log.exception("Subject tracking failed")
            return {"success": False, "video_path": str(video_path), "error": str(exc)}


subject_tracker = SubjectTracker()
