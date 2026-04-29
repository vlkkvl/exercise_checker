"""Squat form checker.

Checks:
1. Knee angle at bottom (~90°)
2. Knee-over-toe alignment (knee x should not go far past toe x)
3. Torso angle (back should stay relatively upright, <45° lean)
"""

import numpy as np
from typing import Any


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _lm(landmarks: list[dict], idx: int) -> np.ndarray:
    lm = landmarks[idx]
    return np.array([lm["x"], lm["y"]])


def analyze(frames_landmarks: list[list[dict]]) -> dict[str, Any]:
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_KNEE, RIGHT_KNEE = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28
    LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX = 31, 32
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

    knee_angles: list[float] = []
    knee_toe_overrides: list[float] = []  # how far knee x exceeds toe x (normalized)
    torso_angles: list[float] = []

    for lms in frames_landmarks:
        if not lms:
            continue

        hip = (_lm(lms, LEFT_HIP) + _lm(lms, RIGHT_HIP)) / 2
        knee = (_lm(lms, LEFT_KNEE) + _lm(lms, RIGHT_KNEE)) / 2
        ankle = (_lm(lms, LEFT_ANKLE) + _lm(lms, RIGHT_ANKLE)) / 2
        foot = (_lm(lms, LEFT_FOOT_INDEX) + _lm(lms, RIGHT_FOOT_INDEX)) / 2
        shoulder = (_lm(lms, LEFT_SHOULDER) + _lm(lms, RIGHT_SHOULDER)) / 2

        knee_angles.append(_angle(hip, knee, ankle))

        # Knee-over-toe: in normalized image coords x goes right.
        # We check both sides independently for better accuracy.
        for k_idx, f_idx in [(LEFT_KNEE, LEFT_FOOT_INDEX), (RIGHT_KNEE, RIGHT_FOOT_INDEX)]:
            k = _lm(lms, k_idx)
            f = _lm(lms, f_idx)
            # positive = knee ahead of toe
            knee_toe_overrides.append(k[0] - f[0])

        # Torso angle: angle between vertical and shoulder-hip line
        # Use angle at hip between shoulder and a point directly above hip
        above_hip = np.array([hip[0], hip[1] - 0.1])  # point above hip
        torso_angles.append(_angle(shoulder, hip, above_hip))

    if not knee_angles:
        return {"passed": False, "feedback": ["No pose detected in the video."]}

    min_knee = min(knee_angles)
    max_knee_toe = max(knee_toe_overrides)
    max_torso = max(torso_angles)

    feedback: list[str] = []
    passed = True

    # Rule 1: knee should reach ~90° at bottom
    if min_knee > 110:
        passed = False
        feedback.append(
            f"Squat deeper — knees only reached {min_knee:.0f}° (aim for ~90°)."
        )

    # Rule 2: knee should not travel far past toes (threshold: 0.05 in normalized coords)
    if max_knee_toe > 0.05:
        passed = False
        feedback.append(
            "Knees are tracking too far over your toes — push your hips back more."
        )

    # Rule 3: torso should not lean forward more than ~45°
    if max_torso > 45:
        passed = False
        feedback.append(
            f"Keep your chest up — torso leaned {max_torso:.0f}° forward at peak."
        )

    if passed:
        feedback.append("Good depth, neutral spine, and knees tracking well.")

    return {"passed": passed, "feedback": feedback}
