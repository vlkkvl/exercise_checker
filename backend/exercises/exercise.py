import numpy as np
from abc import ABC, abstractmethod
from typing import Any

class Exercise(ABC):

    @staticmethod
    def angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))

    @staticmethod
    def lm(landmarks: list[dict], idx: int) -> np.ndarray:
        lm = landmarks[idx]
        return np.array([lm["x"], lm["y"]])

    @abstractmethod
    def analyze(self, frames_landmarks: list[list[dict]]) -> dict[str, Any]:
        pass