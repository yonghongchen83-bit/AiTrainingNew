from __future__ import annotations


def compute_sft_quality_reward(match_score: float, structure_score: float) -> float:
    """Placeholder reward utility for SFT-stage evaluation reporting.

    SFT optimization itself is supervised; this function can be used for post-train scoring.
    """
    return 0.7 * match_score + 0.3 * structure_score
