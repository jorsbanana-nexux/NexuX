from __future__ import annotations

from pathlib import Path
import cv2


def detect_scene_changes(path: Path, start: float = 0.0, end: float | None = None, threshold: float = 0.34, sample_fps: float = 2.0) -> list[dict]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / fps if total_frames > 0 else 0.0
    start = max(0.0, start)
    end = duration if end is None else min(float(end), duration)
    if end <= start:
        cap.release()
        return []
    start_frame = int(start * fps)
    end_frame = int(end * fps)
    step_frames = max(1, int(round(fps / max(sample_fps, 0.5))))
    scenes = [{"start": start}]
    previous = None
    frame_index = 0
    try:
        while frame_index < end_frame:
            ok = cap.grab()
            if not ok:
                break
            current_index = frame_index
            frame_index += 1
            if current_index < start_frame or (current_index - start_frame) % step_frames:
                continue
            ok, frame = cap.retrieve()
            if not ok or frame is None:
                continue
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 90))
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            t = current_index / fps
            if previous is not None:
                score = float(cv2.absdiff(gray, previous).mean()) / 255.0
                if score >= threshold and t - float(scenes[-1]["start"]) >= 0.25:
                    scenes[-1]["end"] = t
                    scenes.append({"start": t, "change_score": round(score, 4)})
            previous = gray
    finally:
        cap.release()
    scenes[-1]["end"] = end
    return [
        {"start": round(float(item["start"]), 3), "end": round(float(item["end"]), 3), "duration": round(float(item["end"] - item["start"]), 3), "change_score": float(item.get("change_score", 0.0))}
        for item in scenes if "end" in item
    ]
