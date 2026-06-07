"""Base interface and helpers for a single test section (phase).

Each test package (e.g. digit_counting_curriculum_v1) defines concrete
subclasses in its own runtime/ folder.  The top-level controller
dispatches to them via this protocol.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

from .models import EpisodeRecord


class TrainingType(Protocol):
    """Interface for one section/phase of a multi-stage test.

    Each section type (SFT, curriculum, …) implements this protocol.
    The config dictionary is the section's own config block from the
    ``phases`` list in test_contract.json.
    """

    def __init__(self, section_cfg: dict[str, Any]) -> None: ...

    def run(
        self,
        *,
        execute_episode: Callable[..., EpisodeRecord],
        register_capability_summary: Callable[..., str],
        test_id: str,
        stage_name: str,
    ) -> dict[str, Any]: ...


# ── Shared helpers ────────────────────────────────────────────────────

def _to_int(cfg: dict[str, Any], key: str, default: int) -> int:
    return int(cfg.get(key, default))


def _to_float(cfg: dict[str, Any], key: str, default: float) -> float:
    return float(cfg.get(key, default))
