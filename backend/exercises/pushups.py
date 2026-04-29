"""Push-up form checker.

Checks:
1. Elbow angle at bottom position (~90°)
2. Back straightness: hip-shoulder-ankle alignment
"""

import numpy as np
from typing import Any


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return the angle at vertex b formed by points a-b-c, in degrees."""
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _lm(landmarks: list[dict], idx: int) -> np.ndarray:
    lm = landmarks[idx]
    return np.array([lm["x"], lm["y"]])


def analyze(frames_landmarks: list[list[dict]]) -> dict[str, Any]:
    """
    frames_landmarks: list of frames, each frame is a list of 33 MediaPipe
                      pose landmark dicts with keys x, y, z, visibility.
    Returns dict with keys: passed (bool), feedback (list[str])
    """
    # MediaPipe landmark indices
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_ELBOW, RIGHT_ELBOW = 13, 14
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28

    elbow_angles: list[float] = []
    back_deviations: list[float] = []

    for lms in frames_landmarks:
        if not lms:
            continue

        # Average left+right for robustness
        shoulder = (_lm(lms, LEFT_SHOULDER) + _lm(lms, RIGHT_SHOULDER)) / 2
        elbow = (_lm(lms, LEFT_ELBOW) + _lm(lms, RIGHT_ELBOW)) / 2
        wrist = (_lm(lms, LEFT_WRIST) + _lm(lms, RIGHT_WRIST)) / 2
        hip = (_lm(lms, LEFT_HIP) + _lm(lms, RIGHT_HIP)) / 2
        ankle = (_lm(lms, LEFT_ANKLE) + _lm(lms, RIGHT_ANKLE)) / 2

        elbow_angles.append(_angle(shoulder, elbow, wrist))

        # Back straightness: angle at hip in shoulder-hip-ankle chain
        # A perfectly straight back → ~180°
        back_angle = _angle(shoulder, hip, ankle)
        back_deviations.append(abs(180.0 - back_angle))

    if not elbow_angles:
        return {"passed": False, "feedback": ["No pose detected in the video."]}

    min_elbow = min(elbow_angles)
    max_back_deviation = max(back_deviations)

    feedback: list[str] = []
    passed = True

    # Rule 1: elbow should reach ~90° at the bottom
    if min_elbow > 110:
        passed = False
        feedback.append(
            f"Go lower — your elbows only reached {min_elbow:.0f}° (aim for ~90°)."
        )
    elif min_elbow < 60:
        passed = False
        feedback.append(
            f"Elbow angle too acute at bottom ({min_elbow:.0f}°) — you may be collapsing your chest."
        )

    # Rule 2: back should stay straight (deviation from 180° < 20°)
    if max_back_deviation > 20:
        passed = False
        feedback.append(
            f"Keep your back flat — detected a {max_back_deviation:.0f}° sag or pike in your hips."
        )

    if passed:
        feedback.append("Great depth and a solid flat back throughout.")

    return {"passed": passed, "feedback": feedback}
