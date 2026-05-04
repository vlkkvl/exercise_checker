"""Shared helpers for backend tests."""
from __future__ import annotations


def make_frame(positions: dict[int, tuple[float, float]], visibility: float = 1.0) -> list[dict]:
    """Build a 33-landmark frame, overriding the indices in ``positions``.

    Indices not in ``positions`` are filled with (0, 0) so the structure is valid
    but won't be referenced by any of the exercises under test.
    """
    frame = [{"x": 0.0, "y": 0.0, "z": 0.0, "visibility": visibility} for _ in range(33)]
    for idx, (x, y) in positions.items():
        frame[idx] = {"x": x, "y": y, "z": 0.0, "visibility": visibility}
    return frame


def mirror(positions: dict[int, tuple[float, float]]) -> dict[int, tuple[float, float]]:
    """Duplicate left-side landmark values onto their right-side counterparts.

    Lets tests specify a single coordinate per body part instead of two.
    """
    pairs = {11: 12, 13: 14, 15: 16, 23: 24, 25: 26, 27: 28, 29: 30, 31: 32}
    out = dict(positions)
    for left, right in pairs.items():
        if left in positions and right not in positions:
            out[right] = positions[left]
        elif right in positions and left not in positions:
            out[left] = positions[right]
    return out
