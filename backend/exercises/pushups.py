"""Push-up form checker.

Checks:
1. Elbow angle at bottom position (~90°)
2. Back straightness: hip-shoulder-ankle alignment
"""
from backend.exercises.exercise import Exercise, Rule


class Pushup(Exercise):

    RULES = [
        Rule("elbow_angle", min, lambda v: v > 110,
             "Go lower — your elbows only reached {value:.0f}° (aim for ~90°)."),
        Rule("elbow_angle", min, lambda v: v < 60,
             "Elbow angle too acute at bottom ({value:.0f}°) — you may be collapsing your chest."),
        Rule("back_deviation", max, lambda v: v > 20,
             "Keep your back flat — detected a {value:.0f}° sag or pike in your hips."),
    ]
    SUCCESS_MESSAGE = "Great depth and a solid flat back throughout."

    def _per_frame(self, lms: list[dict]) -> dict[str, float]:
        shoulder = self.midpoint(lms, self.LEFT_SHOULDER, self.RIGHT_SHOULDER)
        elbow = self.midpoint(lms, self.LEFT_ELBOW, self.RIGHT_ELBOW)
        wrist = self.midpoint(lms, self.LEFT_WRIST, self.RIGHT_WRIST)
        hip = self.midpoint(lms, self.LEFT_HIP, self.RIGHT_HIP)
        ankle = self.midpoint(lms, self.LEFT_ANKLE, self.RIGHT_ANKLE)

        return {
            "elbow_angle": self.angle(shoulder, elbow, wrist),
            "back_deviation": abs(180.0 - self.angle(shoulder, hip, ankle)),
        }
