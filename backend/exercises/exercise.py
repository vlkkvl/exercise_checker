from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Iterable

import numpy as np


@dataclass(frozen=True)
class Rule:
    metric: str
    aggregate: Callable[[Iterable[float]], float]
    is_violation: Callable[[float], bool]
    message: str  # may reference {value}


class Exercise(ABC):
    # MediaPipe pose landmark indices
    NOSE = 0
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_ELBOW, RIGHT_ELBOW = 13, 14
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_KNEE, RIGHT_KNEE = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28
    LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX = 31, 32

    RULES: list[Rule] = []
    SUCCESS_MESSAGE: str = ""

    @staticmethod
    def angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))

    @staticmethod
    def lm(landmarks: list[dict], idx: int) -> np.ndarray:
        p = landmarks[idx]
        return np.array([p["x"], p["y"]])

    @classmethod
    def midpoint(cls, landmarks: list[dict], left_idx: int, right_idx: int) -> np.ndarray:
        return (cls.lm(landmarks, left_idx) + cls.lm(landmarks, right_idx)) / 2

    def analyze(self, frames_landmarks: list[list[dict]]) -> dict[str, Any]:
        per_frame: list[dict[str, float]] = []
        for lms in frames_landmarks:
            if not lms:
                continue
            metrics = self._per_frame(lms)
            if metrics:
                per_frame.append(metrics)

        if not per_frame:
            return {"passed": False, "feedback": ["No pose detected in the video."]}

        feedback: list[str] = []
        passed = True
        for rule in self.RULES:
            value = rule.aggregate(f[rule.metric] for f in per_frame)
            if rule.is_violation(value):
                passed = False
                feedback.append(rule.message.format(value=value))

        if passed:
            feedback.append(self.SUCCESS_MESSAGE)

        return {"passed": passed, "feedback": feedback}

    @abstractmethod
    def _per_frame(self, lms: list[dict]) -> dict[str, float] | None:
        """Return the metrics for one frame, or None to skip the frame."""
