from __future__ import annotations


def compute_confidence_reward(correct: bool, confidence: float) -> float:
    """Brier-style confidence calibration reward.

    Higher is better when confidence aligns with correctness.
    """
    y = 1.0 if correct else 0.0
    brier = (confidence - y) ** 2
    return 1.0 - brier
