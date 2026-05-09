"""Squat form checker.

Checks:
1. Knee angle at bottom (~90°)
2. Knee-over-toe alignment (knee x should not go far past toe x)
3. Torso angle (back should stay relatively upright, <45° lean)
"""
import numpy as np

from backend.exercises.exercise import Exercise, Rule


class Squat(Exercise):

    RULES = [
        Rule("knee_angle", min, lambda v: v > 110,
             "Squat deeper — knees only reached {value:.0f}° (aim for ~90°)."),
        Rule("knee_toe", max, lambda v: v > 0.05,
             "Knees are tracking too far over your toes — push your hips back more."),
        Rule("torso_angle", max, lambda v: v > 45,
             "Keep your chest up — torso leaned {value:.0f}° forward at peak."),
    ]
    SUCCESS_MESSAGE = "Good depth, neutral spine, and knees tracking well."

    def _per_frame(self, lms: list[dict]) -> dict[str, float]:
        hip = self.midpoint(lms, self.LEFT_HIP, self.RIGHT_HIP)
        knee = self.midpoint(lms, self.LEFT_KNEE, self.RIGHT_KNEE)
        ankle = self.midpoint(lms, self.LEFT_ANKLE, self.RIGHT_ANKLE)
        shoulder = self.midpoint(lms, self.LEFT_SHOULDER, self.RIGHT_SHOULDER)

        knee_toe = max(
            self._knee_past_toe(lms, self.LEFT_KNEE, self.LEFT_ANKLE, self.LEFT_FOOT_INDEX),
            self._knee_past_toe(lms, self.RIGHT_KNEE, self.RIGHT_ANKLE, self.RIGHT_FOOT_INDEX),
        )

        above_hip = hip + np.array([0.0, -0.1, 0.0])

        return {
            "knee_angle": self.angle(hip, knee, ankle),
            "knee_toe": knee_toe,
            "torso_angle": self.angle(shoulder, hip, above_hip),
        }

    def _knee_past_toe(self, lms: list[dict], knee_idx: int, ankle_idx: int, toe_idx: int) -> float:
        """Signed distance the knee has travelled past the toe along the foot's pointing
        direction in the horizontal (xz) plane. Positive means knee is in front of toe."""
        knee = self.horizontal(self.lm(lms, knee_idx))
        ankle = self.horizontal(self.lm(lms, ankle_idx))
        toe = self.horizontal(self.lm(lms, toe_idx))
        foot_dir = toe - ankle
        foot_len = float(np.linalg.norm(foot_dir))
        if foot_len < 1e-6:
            return 0.0
        return float(np.dot(knee - toe, foot_dir) / foot_len)
