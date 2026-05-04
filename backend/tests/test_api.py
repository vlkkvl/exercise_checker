"""End-to-end tests for the FastAPI surface, with the pose extractor mocked."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app
from backend.tests.helpers import make_frame, mirror


@pytest.fixture
def client():
    return TestClient(app)


def _good_pushup_frame():
    return make_frame(mirror({
        11: (0.3, 0.5),  # shoulder
        13: (0.3, 0.6),  # elbow → 90° at elbow
        15: (0.4, 0.6),  # wrist
        23: (0.5, 0.5),  # hip
        27: (0.7, 0.5),  # ankle → back 180°
    }))


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_rejects_non_video_content_type(client):
    r = client.post(
        "/analyze",
        data={"exercise": "pushups"},
        files={"video": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert "must be a video" in r.json()["detail"]


def test_analyze_rejects_unknown_exercise(client):
    # FastAPI's Literal validation rejects this with 422 before we reach extract_landmarks
    r = client.post(
        "/analyze",
        data={"exercise": "running"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 422


def test_analyze_no_pose_detected(monkeypatch, client):
    monkeypatch.setattr(main_module, "extract_landmarks", lambda _: [[], [], []])
    r = client.post(
        "/analyze",
        data={"exercise": "pushups"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 422
    assert "No person detected" in r.json()["detail"]


def test_analyze_extractor_failure_returns_422(monkeypatch, client):
    def boom(_):
        raise ValueError("corrupt video")

    monkeypatch.setattr(main_module, "extract_landmarks", boom)
    r = client.post(
        "/analyze",
        data={"exercise": "pushups"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 422
    assert "corrupt video" in r.json()["detail"]


def test_analyze_pushups_success(monkeypatch, client):
    frames = [_good_pushup_frame()] * 3
    monkeypatch.setattr(main_module, "extract_landmarks", lambda _: frames)

    r = client.post(
        "/analyze",
        data={"exercise": "pushups"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["exercise"] == "pushups"
    assert body["passed"] is True
    assert body["feedback"] == ["Great depth and a solid flat back throughout."]


def test_analyze_dispatches_to_correct_exercise(monkeypatch, client):
    """The endpoint should route to the BicepCurl analyzer when exercise=bicep_curls."""
    # frames that pass for bicep curls (full ROM, no drift)
    extended = make_frame(mirror({11: (0.5, 0.4), 13: (0.5, 0.6), 15: (0.5, 0.8)}))
    contracted = make_frame(mirror({11: (0.5, 0.4), 13: (0.5, 0.6), 15: (0.5, 0.42)}))
    monkeypatch.setattr(main_module, "extract_landmarks", lambda _: [extended, contracted])

    r = client.post(
        "/analyze",
        data={"exercise": "bicep_curls"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["exercise"] == "bicep_curls"
    assert body["passed"] is True


def test_analyze_temp_file_is_cleaned_up(monkeypatch, client, tmp_path):
    captured: list[str] = []

    def fake_extract(path):
        captured.append(str(path))
        # confirm the file is on disk while we're processing
        from pathlib import Path
        assert Path(path).exists()
        return [_good_pushup_frame()]

    monkeypatch.setattr(main_module, "extract_landmarks", fake_extract)
    r = client.post(
        "/analyze",
        data={"exercise": "pushups"},
        files={"video": ("a.mp4", b"FAKE", "video/mp4")},
    )
    assert r.status_code == 200
    assert captured, "extract_landmarks was not called"

    from pathlib import Path
    # by the time the response returns, the temp file should be gone
    assert not Path(captured[0]).exists()
