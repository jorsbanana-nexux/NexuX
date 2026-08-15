"""AGENT_11_SCENE_SEGMENTER - compatibility adapter over Local-First V5 vision."""

from utils.logger import get_logger
from v5_bridge import detect_scene_changes

log = get_logger("agent_11")


class SceneSegmenter:
    async def segment_video(self, video_path, max_duration=None):
        log.info("Segmenting real media: %s", video_path)
        try:
            import cv2

            cap = cv2.VideoCapture(str(video_path))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
            frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
            cap.release()
            duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0
            if max_duration is not None:
                duration = min(duration, float(max_duration))
            scenes = detect_scene_changes(video_path, 0.0, duration or None)
            return {
                "success": True,
                "video_path": str(video_path),
                "total_duration": duration,
                "fps": fps,
                "segment_count": len(scenes),
                "segments": scenes,
            }
        except Exception as exc:
            log.exception("Scene segmentation failed")
            return {"success": False, "video_path": str(video_path), "error": str(exc)}


scene_segmenter = SceneSegmenter()
