"""Extract per-frame MediaPipe pose landmarks from a video file.

Uses the MediaPipe Tasks API (PoseLandmarker) with VIDEO running mode.
Requires the pose landmarker model asset; download it once with:
    python -c "from pose_extractor import download_model; download_model()"
or place pose_landmarker_full.task next to this file.
"""

import logging
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp

logger = logging.getLogger("exercise_checker.pose")

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)
_DEFAULT_MODEL = Path(__file__).parent / "pose_landmarker_full.task"


def download_model(dest: Path = _DEFAULT_MODEL) -> Path:
    """Download the pose landmarker model if not already present."""
    if not dest.exists():
        logger.info("Downloading pose landmarker model to %s …", dest)
        t0 = time.perf_counter()
        urllib.request.urlretrieve(_MODEL_URL, dest)
        logger.info(
            "Model download complete (%.1f MB in %.2fs)",
            dest.stat().st_size / (1024 * 1024), time.perf_counter() - t0,
        )
    return dest


def extract_landmarks(
    video_path: str | Path,
    model_path: str | Path | None = None,
) -> list[list[dict]]:
    """
    Returns a list of frames. Each frame is either:
    - a list of 33 landmark dicts (keys: x, y, z, visibility)
    - an empty list if no pose was detected in that frame
    """
    model_path = Path(model_path) if model_path else download_model()
    logger.info("Using pose model: %s (exists=%s)", model_path, model_path.exists())

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    logger.info(
        "Video opened: %s | fps=%.2f total_frames=%d est_duration=%.1fs",
        video_path, fps, total_frames, (total_frames / fps) if fps else 0,
    )

    frames: list[list[dict]] = []
    frame_idx = 0
    detected_count = 0

    landmarker_init_start = time.perf_counter()
    with PoseLandmarker.create_from_options(options) as landmarker:
        logger.info(
            "PoseLandmarker initialized in %.2fs",
            time.perf_counter() - landmarker_init_start,
        )
        loop_start = time.perf_counter()
        last_progress_log = loop_start

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(frame_idx * 1000 / fps)

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                lms = [
                    {
                        "x": lm.x,
                        "y": lm.y,
                        "z": lm.z,
                        "visibility": lm.visibility,
                    }
                    for lm in result.pose_landmarks[0]
                ]
                frames.append(lms)
                detected_count += 1
            else:
                frames.append([])

            frame_idx += 1

            # progress log roughly every second of wall clock to bound noise
            now = time.perf_counter()
            if now - last_progress_log >= 1.0:
                logger.info(
                    "  …processed %d/%s frames (%.1f fps, %d with pose)",
                    frame_idx,
                    total_frames or "?",
                    frame_idx / (now - loop_start) if now > loop_start else 0,
                    detected_count,
                )
                last_progress_log = now

        loop_elapsed = time.perf_counter() - loop_start

    cap.release()
    logger.info(
        "Inference complete: %d frames in %.2fs (%.1f fps avg, %d with pose)",
        frame_idx, loop_elapsed,
        frame_idx / loop_elapsed if loop_elapsed > 0 else 0,
        detected_count,
    )
    return frames
