from __future__ import annotations

from typing import Any


def simulate_batch(
    batch: list[dict[str, Any]],
    step_index: int,
    contract: dict[str, Any],
    seed: int,
) -> list[dict[str, Any]]:
    """Return deterministic simulated outputs for RLHF confidence checks.

    This simulator is intentionally test-local so each test package can evolve
    independently without central agent branching complexity.
    """
    _ = (step_index, contract, seed)
    outputs: list[dict[str, Any]] = []
    for sample in batch:
        outputs.append(
            {
                "response": sample.get("response", ""),
                "confidence": float(sample.get("confidence", 0.5)),
                "correct": bool(sample.get("correct", False)),
            }
        )
    return outputs
