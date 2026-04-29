"""Bicep curl form checker.

Checks:
1. Elbow stays fixed at side (elbow x drift relative to shoulder x)
2. Full range of motion: angle goes low (~150°+ extended) and high (~40°- contracted)
"""
from abc import ABC
from typing import Any
from backend.exercises.exercise import Exercise

class BicepCurl(Exercise, ABC):
    def analyze(self, frames_landmarks: list[list[dict]]) -> dict[str, Any]:
        LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
        LEFT_ELBOW, RIGHT_ELBOW = 13, 14
        LEFT_WRIST, RIGHT_WRIST = 15, 16

        elbow_angles: list[float] = []
        # Elbow drift: horizontal distance between elbow and shoulder (normalized)
        elbow_drifts: list[float] = []

        for lms in frames_landmarks:
            if not lms:
                continue

            # Process each arm independently, keep the one with better visibility
            results = []
            for s_idx, e_idx, w_idx in [
                (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
                (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
            ]:
                vis = lms[e_idx].get("visibility", 0)
                if vis < 0.5:
                    continue
                shoulder = self.lm(lms, s_idx)
                elbow = self.lm(lms, e_idx)
                wrist = self.lm(lms, w_idx)
                ang = self.angle(shoulder, elbow, wrist)
                drift = abs(elbow[0] - shoulder[0])
                results.append((ang, drift))

            if results:
                # Use average if both arms visible
                elbow_angles.append(float(np.mean([r[0] for r in results])))
                elbow_drifts.append(float(np.mean([r[1] for r in results])))

        if not elbow_angles:
            return {"passed": False, "feedback": ["No pose detected in the video."]}

        min_angle = min(elbow_angles)   # fully contracted
        max_angle = max(elbow_angles)   # fully extended
        max_drift = max(elbow_drifts)

        feedback: list[str] = []
        passed = True

        # Rule 1: full extension at bottom (> 150°)
        if max_angle < 140:
            passed = False
            feedback.append(
                f"Extend fully at the bottom — max angle was {max_angle:.0f}° (aim for ~150°+)."
            )

        # Rule 2: full contraction at top (< 50°)
        if min_angle > 60:
            passed = False
            feedback.append(
                f"Curl higher — minimum angle was {min_angle:.0f}° (aim for ~40–50°)."
            )

        # Rule 3: elbow drift (threshold: 0.08 in normalized coords)
        if max_drift > 0.08:
            passed = False
            feedback.append(
                "Keep your elbows pinned at your sides — they're swinging outward."
            )

        if passed:
            feedback.append("Full range of motion with elbows staying fixed — nice work.")

        return {"passed": passed, "feedback": feedback}
