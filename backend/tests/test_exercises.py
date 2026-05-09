"""Tests for the Exercise base pipeline and each form-checker subclass.

Synthetic landmark fixtures are constructed so that target angles fall on
specific, hand-verified values. Comments next to each fixture record the
geometry being tested.
"""
from __future__ import annotations

import math

import pytest

from backend.exercises.exercise import Exercise, Rule
from backend.exercises.bicep_curls import BicepCurl
from backend.exercises.pushups import Pushup
from backend.exercises.squats import Squat
from backend.tests.helpers import make_frame, mirror


# ------------------------------------------------------------------ base utils

class _Dummy(Exercise):
    """Minimal concrete subclass for exercising base pipeline behavior."""

    RULES = [
        Rule("v", max, lambda x: x > 10, "too big: {value:.0f}"),
    ]
    SUCCESS_MESSAGE = "all good"

    def _per_frame(self, lms):
        # the helper sets visibility=1.0 by default; we just read landmark 0.
        x = lms[0]["x"]
        if x < 0:
            return None
        return {"v": x}


def test_angle_right_angle():
    import numpy as np
    a = np.array([0.0, 1.0])
    b = np.array([0.0, 0.0])
    c = np.array([1.0, 0.0])
    assert Exercise.angle(a, b, c) == pytest.approx(90.0, abs=1e-3)


def test_angle_straight():
    import numpy as np
    a = np.array([-1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([1.0, 0.0])
    # tiny epsilon in the formula prevents exact 180°; tolerance reflects that.
    assert Exercise.angle(a, b, c) == pytest.approx(180.0, abs=1e-2)


def test_midpoint():
    frame = make_frame({11: (0.2, 0.4), 12: (0.4, 0.6)})
    mp = Exercise.midpoint(frame, 11, 12)
    assert mp[0] == pytest.approx(0.3)
    assert mp[1] == pytest.approx(0.5)


def test_analyze_no_frames_returns_no_pose_detected():
    res = _Dummy().analyze([])
    assert res == {"passed": False, "feedback": ["No pose detected in the video."]}


def test_analyze_skips_empty_frames():
    res = _Dummy().analyze([[], [], []])
    assert res["passed"] is False
    assert res["feedback"] == ["No pose detected in the video."]


def test_analyze_skips_when_per_frame_returns_none():
    # x < 0 → _per_frame returns None
    frame = make_frame({0: (-1.0, 0.0)})
    res = _Dummy().analyze([frame, frame])
    assert res["feedback"] == ["No pose detected in the video."]


def test_analyze_passes_emits_success_message():
    frame = make_frame({0: (5.0, 0.0)})  # v=5, below threshold
    res = _Dummy().analyze([frame, frame])
    assert res["passed"] is True
    assert res["feedback"] == ["all good"]


def test_analyze_fails_emits_violation_message_with_value():
    frame_low = make_frame({0: (5.0, 0.0)})
    frame_high = make_frame({0: (42.0, 0.0)})
    res = _Dummy().analyze([frame_low, frame_high])
    assert res["passed"] is False
    assert res["feedback"] == ["too big: 42"]


def test_analyze_drops_invalid_frames_but_keeps_valid_ones():
    # mix: empty frame, None-producing frame, valid frame → only valid counts
    frame_invalid = make_frame({0: (-1.0, 0.0)})
    frame_valid = make_frame({0: (3.0, 0.0)})
    res = _Dummy().analyze([[], frame_invalid, frame_valid])
    assert res["passed"] is True


# ------------------------------------------------------------------ pushups

def _pushup_frame(elbow_xy, wrist_xy, hip_xy=(0.5, 0.5), ankle_xy=(0.7, 0.5),
                  shoulder_xy=(0.3, 0.5)):
    return make_frame(mirror({
        11: shoulder_xy,
        13: elbow_xy,
        15: wrist_xy,
        23: hip_xy,
        27: ankle_xy,
    }))


def test_pushup_good_form_passes():
    # elbow 90°, back straight (180°)
    frame = _pushup_frame(elbow_xy=(0.3, 0.6), wrist_xy=(0.4, 0.6))
    res = Pushup().analyze([frame] * 3)
    assert res["passed"] is True
    assert res["feedback"] == [Pushup.SUCCESS_MESSAGE]


def test_pushup_not_deep_enough_fails():
    # arm nearly straight → 180°  > 110°
    frame = _pushup_frame(elbow_xy=(0.35, 0.5), wrist_xy=(0.45, 0.5))
    res = Pushup().analyze([frame])
    assert res["passed"] is False
    assert any("Go lower" in msg for msg in res["feedback"])


def test_pushup_too_acute_fails():
    # elbow ~45° (< 60°)
    frame = _pushup_frame(
        elbow_xy=(0.5, 0.5),
        wrist_xy=(0.5, 0.4),
        shoulder_xy=(0.4, 0.4),
        hip_xy=(0.5, 0.4),
        ankle_xy=(0.6, 0.4),
    )
    res = Pushup().analyze([frame])
    assert res["passed"] is False
    assert any("too acute" in msg for msg in res["feedback"])


def test_pushup_back_sag_fails():
    # elbow good (90°), hips sag → back angle 90°, deviation 90°
    frame = _pushup_frame(
        elbow_xy=(0.3, 0.6),
        wrist_xy=(0.4, 0.6),
        hip_xy=(0.5, 0.7),  # sag
    )
    res = Pushup().analyze([frame])
    assert res["passed"] is False
    assert any("back flat" in msg for msg in res["feedback"])


def test_pushup_multiple_violations_all_reported():
    # not-deep + back sag in same frame
    frame = _pushup_frame(
        elbow_xy=(0.35, 0.5),
        wrist_xy=(0.45, 0.5),
        hip_xy=(0.5, 0.7),
    )
    res = Pushup().analyze([frame])
    assert res["passed"] is False
    assert len(res["feedback"]) == 2


# ------------------------------------------------------------------ squats

def _squat_frame(
    shoulder_xy=(0.5, 0.2),
    hip_xy=(0.5, 0.4),
    knee_xy=(0.5, 0.6),
    ankle_xy=(0.7, 0.6),
    foot_xy=(0.72, 0.65),
):
    return make_frame(mirror({
        11: shoulder_xy,
        23: hip_xy,
        25: knee_xy,
        27: ankle_xy,
        31: foot_xy,
    }))


def test_squat_good_form_passes():
    frame = _squat_frame()
    res = Squat().analyze([frame] * 3)
    assert res["passed"] is True
    assert res["feedback"] == [Squat.SUCCESS_MESSAGE]


def test_squat_too_shallow_fails():
    # legs almost straight → ~180°
    frame = _squat_frame(
        hip_xy=(0.5, 0.3),
        knee_xy=(0.5, 0.5),
        ankle_xy=(0.5, 0.7),
        foot_xy=(0.55, 0.75),
    )
    res = Squat().analyze([frame])
    assert res["passed"] is False
    assert any("Squat deeper" in msg for msg in res["feedback"])


def test_squat_knee_over_toe_fails():
    # foot points +x (ankle 0.7, toe 0.72); knee at 0.82 → 0.1 past toe along foot dir (>0.05 threshold)
    frame = _squat_frame(knee_xy=(0.82, 0.6))
    res = Squat().analyze([frame])
    assert res["passed"] is False
    assert any("knees" in msg.lower() for msg in res["feedback"])


def test_squat_torso_lean_fails():
    # shoulder pulled forward → torso angle ~76°
    frame = _squat_frame(shoulder_xy=(0.9, 0.3))
    res = Squat().analyze([frame])
    assert res["passed"] is False
    assert any("chest up" in msg for msg in res["feedback"])


# ------------------------------------------------------------------ bicep curls

def _curl_frame(elbow_xy, wrist_xy, shoulder_xy=(0.5, 0.4), visibility=1.0):
    return make_frame(
        mirror({11: shoulder_xy, 13: elbow_xy, 15: wrist_xy}),
        visibility=visibility,
    )


def test_bicep_curl_full_rom_passes():
    extended = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.5, 0.8))   # 180°
    contracted = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.5, 0.42)) # ~0°
    res = BicepCurl().analyze([extended, contracted])
    assert res["passed"] is True
    assert res["feedback"] == [BicepCurl.SUCCESS_MESSAGE]


def test_bicep_curl_insufficient_extension_fails():
    contracted = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.5, 0.42))
    half_ext = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.6, 0.65))  # ~117°
    res = BicepCurl().analyze([contracted, half_ext])
    assert res["passed"] is False
    assert any("Extend fully" in msg for msg in res["feedback"])


def test_bicep_curl_insufficient_contraction_fails():
    extended = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.5, 0.8))
    half_curl = _curl_frame(elbow_xy=(0.5, 0.6), wrist_xy=(0.7, 0.6))  # 90°
    res = BicepCurl().analyze([extended, half_curl])
    assert res["passed"] is False
    assert any("Curl higher" in msg for msg in res["feedback"])


def test_bicep_curl_elbow_drift_fails():
    # elbow pulled out from shoulder by 0.2 in both frames; full ROM otherwise
    extended = _curl_frame(elbow_xy=(0.7, 0.6), wrist_xy=(0.9, 0.8))
    contracted = _curl_frame(elbow_xy=(0.7, 0.6), wrist_xy=(0.5, 0.4))
    res = BicepCurl().analyze([extended, contracted])
    assert res["passed"] is False
    assert any("elbows pinned" in msg for msg in res["feedback"])


def test_bicep_curl_low_visibility_skips_frames():
    # visibility below threshold → _per_frame returns None for every frame
    frame = _curl_frame(
        elbow_xy=(0.5, 0.6),
        wrist_xy=(0.5, 0.8),
        visibility=0.2,
    )
    res = BicepCurl().analyze([frame, frame])
    assert res == {"passed": False, "feedback": ["No pose detected in the video."]}


def test_bicep_curl_uses_only_visible_arm():
    # left arm visible (full ROM), right arm hidden — should still pass
    extended = make_frame({
        11: (0.5, 0.4), 13: (0.5, 0.6), 15: (0.5, 0.8),  # left visible
        12: (0.5, 0.4), 14: (0.5, 0.6), 16: (0.5, 0.8),  # values present but…
    })
    # set right elbow visibility low specifically
    extended[14]["visibility"] = 0.1
    contracted = make_frame({
        11: (0.5, 0.4), 13: (0.5, 0.6), 15: (0.5, 0.42),
        12: (0.5, 0.4), 14: (0.5, 0.6), 16: (0.5, 0.42),
    })
    contracted[14]["visibility"] = 0.1
    res = BicepCurl().analyze([extended, contracted])
    assert res["passed"] is True
