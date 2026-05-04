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
            self.lm(lms, self.LEFT_KNEE)[0] - self.lm(lms, self.LEFT_FOOT_INDEX)[0],
            self.lm(lms, self.RIGHT_KNEE)[0] - self.lm(lms, self.RIGHT_FOOT_INDEX)[0],
        )

        above_hip = np.array([hip[0], hip[1] - 0.1])

        return {
            "knee_angle": self.angle(hip, knee, ankle),
            "knee_toe": knee_toe,
            "torso_angle": self.angle(shoulder, hip, above_hip),
        }
