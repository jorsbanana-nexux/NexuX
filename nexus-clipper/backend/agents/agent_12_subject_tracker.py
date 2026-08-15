"""AGENT_12_SUBJECT_TRACKER - compatibility adapter over Local-First V5 vision."""

from utils.logger import get_logger

log = get_logger("agent_12")


class SubjectTracker:
    async def detect_subjects(self, video_path):
        log.info("Detecting real subjects: %s", video_path)
        try:
            from local_first_v5.vision_quality import detect_face_subjects
        except ImportError:
            try:
                from vision_quality import detect_face_subjects
            except ImportError as exc:
                return {"success": False, "video_path": str(video_path), "error": str(exc)}
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
