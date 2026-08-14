"""
Nexus-Clipper Premium v4.0 — Face & Scene Analysis
===================================================
MediaPipe face detection, scene change detection,
person tracking, screen share detection.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .constants import OUTPUT_DIR
from .utils import retry

log = logging.getLogger("nexus.vision")


def analyze_faces(
    video_path: Path,
    job_id: str,
    sample_every: int = 15,
) -> List[Dict]:
    """Detect faces in video using MediaPipe.
    
    Args:
        video_path: Path to video file
        job_id: Job identifier
        sample_every: Sample every N frames (higher = faster but less accurate)
    
    Returns:
        List of face detection results per sampled frame
    """
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        log.warning("[FaceTrack] OpenCV/MediaPipe not installed. Skipping.")
        return []

    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    mp_face = mp.solutions.face_detection
    face_detector = mp_face.FaceDetection(
        model_selection=1,           # 1 = full-range (better for varied distances)
        min_detection_confidence=0.5)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log.warning(f"[FaceTrack] Cannot open video: {video_path}")
        face_detector.close()
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    log.info(f"[FaceTrack] Analyzing ({fps:.1f}fps, {total_frames} frames, "
             f"sampling every {sample_every})...")

    face_data = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detector.process(frame_rgb)
            faces = []

            if results.detections:
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    faces.append({
                        "x": max(0.0, bbox.xmin),
                        "y": max(0.0, bbox.ymin),
                        "w": min(1.0, max(0.0, bbox.width)),
                        "h": min(1.0, max(0.0, bbox.height)),
                        "score": round(float(det.score[0]) if det.score else 1.0, 3),
                    })

            face_data.append({
                "time": round(frame_idx / fps, 2),
                "frame": frame_idx,
                "faces": faces,
                "face_count": len(faces),
                "video_w": width,
                "video_h": height,
            })

        frame_idx += 1

    cap.release()
    face_detector.close()

    # Save
    fpath = work_dir / "face_tracking.json"
    with open(fpath, "w") as f:
        json.dump(face_data, f, indent=2)

    frames_with_faces = sum(1 for fd in face_data if fd["faces"])
    log.info(f"[FaceTrack] Done: {len(face_data)} samples, "
             f"{frames_with_faces} with faces ({100*frames_with_faces/max(len(face_data),1):.0f}%)")
    return face_data


def detect_scene_changes(
    video_path: Path,
    job_id: str,
    threshold: float = 30.0,
) -> List[Dict]:
    """Detect scene changes using frame difference analysis.
    
    Args:
        video_path: Path to video file
        job_id: Job identifier
        threshold: Difference threshold for scene change (lower = more sensitive)
    
    Returns:
        List of scene change timestamps
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        log.warning("[SceneDetect] OpenCV not installed. Skipping.")
        return []

    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    scenes = []
    prev_frame = None
    frame_idx = 0

    log.info(f"[SceneDetect] Scanning for scene changes...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process every 10th frame for performance
        if frame_idx % 10 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))  # Downscale for speed

            if prev_frame is not None:
                diff = np.mean(np.abs(gray.astype(float) - prev_frame.astype(float)))
                if diff > threshold:
                    scenes.append({
                        "time": round(frame_idx / fps, 2),
                        "frame": frame_idx,
                        "diff_score": round(float(diff), 1),
                    })

            prev_frame = gray.copy()

        frame_idx += 1

    cap.release()

    fpath = work_dir / "scene_changes.json"
    with open(fpath, "w") as f:
        json.dump(scenes, f, indent=2)

    log.info(f"[SceneDetect] Found {len(scenes)} scene changes")
    return scenes


def detect_screen_share(
    video_path: Path,
    job_id: str,
    sample_every: int = 30,
) -> List[Dict]:
    """Detect screen shares / presentations in video.
    
    Uses edge detection to identify UI elements typical of screen recordings.
    
    Args:
        video_path: Path to video file
        job_id: Job identifier
        sample_every: Sample every N frames
    
    Returns:
        List of screen share detection results
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        log.warning("[ScreenDetect] OpenCV not installed. Skipping.")
        return []

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    results = []
    frame_idx = 0
    log.info(f"[ScreenDetect] Scanning for screen shares...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Edge detection — screens have many straight edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.mean(edges > 0)
            
            # Check for large uniform regions (typical of screen shares)
            variance = np.var(gray.astype(float))
            is_ui = edge_density > 0.15 and variance < 3000

            results.append({
                "time": round(frame_idx / fps, 2),
                "frame": frame_idx,
                "edge_density": round(float(edge_density), 4),
                "variance": round(float(variance), 1),
                "is_screen_share": is_ui,
            })

        frame_idx += 1

    cap.release()

    # Save
    fpath = OUTPUT_DIR / job_id / "screen_shares.json"
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "w") as f:
        json.dump(results, f, indent=2)

    screens = sum(1 for r in results if r["is_screen_share"])
    log.info(f"[ScreenDetect] Done: {screens}/{len(results)} frames are screen shares")
    return results
