"""Exercise Checker — FastAPI backend.

Single endpoint: POST /analyze
Accepts a video file + exercise type, returns form analysis.
"""

import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pose_extractor import extract_landmarks
from exercises import pushups, squats, bicep_curls

app = FastAPI(title="Exercise Checker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

ExerciseType = Literal["pushups", "squats", "bicep_curls"]

EXERCISE_ANALYZERS = {
    "pushups": pushups.analyze,
    "squats": squats.analyze,
    "bicep_curls": bicep_curls.analyze,
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
    # Validate content type loosely
    if video.content_type and not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video.")

    content = await video.read()

    if len(content) > MAX_VIDEO_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Video too large. Maximum size is {MAX_VIDEO_BYTES // (1024*1024)} MB.",
        )

    suffix = Path(video.filename or "upload.mp4").suffix or ".mp4"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        frames_landmarks = extract_landmarks(tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to process video: {exc}")
    finally:
        os.unlink(tmp_path)

    # Check that at least some frames had a detected pose
    detected = [f for f in frames_landmarks if f]
    if not detected:
        raise HTTPException(
            status_code=422,
            detail="No person detected in the video. Ensure you are clearly visible.",
        )

    analyzer = EXERCISE_ANALYZERS[exercise]
    result = analyzer(frames_landmarks)

    return AnalysisResult(
        exercise=exercise,
        passed=result["passed"],
        feedback=result["feedback"],
    )
