from __future__ import annotations

from typing import Any


def simulate_batch(
    batch: list[dict[str, Any]],
    step_index: int,
    contract: dict[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    """Return deterministic simulated outputs for SFT pattern checks."""
    _ = (step_index, contract, seed)
    outputs: list[dict[str, Any]] = []
    for sample in batch:
        response = sample.get("response", "")
        outputs.append(
            {
                "response": response,
                "confidence": 0.95,
                "correct": True,
            }
        )
    return outputs
