"""Bicep curl form checker.

Checks:
1. Elbow stays fixed at side (elbow x drift relative to shoulder x)
2. Full range of motion: angle goes low (~150°+ extended) and high (~40°- contracted)
"""
import numpy as np

from backend.exercises.exercise import Exercise, Rule


class BicepCurl(Exercise):

    VISIBILITY_THRESHOLD = 0.5

    RULES = [
        Rule("elbow_angle", max, lambda v: v < 140,
             "Extend fully at the bottom — max angle was {value:.0f}° (aim for ~150°+)."),
        Rule("elbow_angle", min, lambda v: v > 60,
             "Curl higher — minimum angle was {value:.0f}° (aim for ~40–50°)."),
        Rule("elbow_drift", max, lambda v: v > 0.08,
             "Keep your elbows pinned at your sides — they're swinging outward."),
    ]
    SUCCESS_MESSAGE = "Full range of motion with elbows staying fixed — nice work."

    def _per_frame(self, lms: list[dict]) -> dict[str, float] | None:
        arms = [
            (self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST),
            (self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST),
        ]
        angles: list[float] = []
        drifts: list[float] = []

        for s_idx, e_idx, w_idx in arms:
            if lms[e_idx].get("visibility", 0) < self.VISIBILITY_THRESHOLD:
                continue
            shoulder = self.lm(lms, s_idx)
            elbow = self.lm(lms, e_idx)
            wrist = self.lm(lms, w_idx)
            angles.append(self.angle(shoulder, elbow, wrist))
            drifts.append(float(np.linalg.norm(self.horizontal(elbow) - self.horizontal(shoulder))))

        if not angles:
            return None

        return {
            "elbow_angle": float(np.mean(angles)),
            "elbow_drift": float(np.mean(drifts)),
        }
