"""Exercise Checker — FastAPI backend.

Single endpoint: POST /analyze
Accepts a video file + exercise type, returns form analysis.
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.pose_extractor import extract_landmarks
from backend.exercises.exercise import Exercise
from backend.exercises.pushups import Pushup
from backend.exercises.squats import Squat
from backend.exercises.bicep_curls import BicepCurl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("exercise_checker")
logger.setLevel(logging.INFO)

app = FastAPI(title="Exercise Checker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

ExerciseType = Literal["pushups", "squats", "bicep_curls"]

EXERCISE_ANALYZERS: dict[str, Exercise] = {
    "pushups": Pushup(),
    "squats": Squat(),
    "bicep_curls": BicepCurl(),
}

MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_DURATION_SECONDS = 60


class AnalysisResult(BaseModel):
    exercise: str
    passed: bool
    feedback: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(
    exercise: ExerciseType = Form(...),
    video: UploadFile = File(...),
) -> AnalysisResult:
    request_started = time.perf_counter()
    logger.info(
        "POST /analyze received exercise=%s filename=%s content_type=%s",
        exercise, video.filename, video.content_type,
    )

    if video.content_type and not video.content_type.startswith("video/"):
        logger.warning("Rejected non-video content_type=%s", video.content_type)
        raise HTTPException(status_code=400, detail="Uploaded file must be a video.")

    read_start = time.perf_counter()
    content = await video.read()
    logger.info(
        "Read upload: %.2f MB in %.2fs",
        len(content) / (1024 * 1024), time.perf_counter() - read_start,
    )

    if len(content) > MAX_VIDEO_BYTES:
        logger.warning("Rejected oversized upload: %d bytes", len(content))
        raise HTTPException(
            status_code=413,
            detail=f"Video too large. Maximum size is {MAX_VIDEO_BYTES // (1024*1024)} MB.",
        )

    suffix = Path(video.filename or "upload.mp4").suffix or ".mp4"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    logger.info("Wrote temp file: %s", tmp_path)

    try:
        extract_start = time.perf_counter()
        frames_landmarks = extract_landmarks(tmp_path)
        logger.info(
            "extract_landmarks returned %d frames in %.2fs",
            len(frames_landmarks), time.perf_counter() - extract_start,
        )
    except Exception as exc:
        logger.exception("extract_landmarks failed for %s", tmp_path)
        raise HTTPException(status_code=422, detail=f"Failed to process video: {exc}")
    finally:
        os.unlink(tmp_path)

    detected = [f for f in frames_landmarks if f]
    logger.info(
        "Pose detected in %d/%d frames", len(detected), len(frames_landmarks),
    )
    if not detected:
        raise HTTPException(
            status_code=422,
            detail="No person detected in the video. Ensure you are clearly visible.",
        )

    analyze_start = time.perf_counter()
    analyzer = EXERCISE_ANALYZERS[exercise]
    result = analyzer.analyze(frames_landmarks)
    logger.info(
        "Analyzer %s finished in %.3fs: passed=%s feedback_count=%d",
        exercise, time.perf_counter() - analyze_start,
        result["passed"], len(result["feedback"]),
    )

    logger.info(
        "POST /analyze done in %.2fs total",
        time.perf_counter() - request_started,
    )
    return AnalysisResult(
        exercise=exercise,
        passed=result["passed"],
        feedback=result["feedback"],
    )
