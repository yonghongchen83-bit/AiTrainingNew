"""Top-level test controller — dispatches phases to dedicated section classes."""

from typing import Any, Callable

from training.materials.digit_counting_curriculum_v1.runtime.sft_training import SftTraining
from training.materials.digit_counting_curriculum_v1.runtime.curriculum_training import CurriculumTraining


# ── Phase dispatch registry ──────────────────────────────────────────

_PHASE_CLASSES: dict[str, type] = {
    "sft": SftTraining,
    "curriculum": CurriculumTraining,
}


def run_test_loop(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    """Execute all phases defined in the contract, dispatching each to its class."""
    test_id = str(contract.get("test_id", "digit_counting"))
    specific_cfg = contract.get("test_specific", {})
    phases = _normalize_phases(specific_cfg.get("phases", []))
    phase_summaries: list[dict[str, Any]] = []

    for idx, phase_cfg in enumerate(phases):
        ptype = phase_cfg["type"]
        cls = _PHASE_CLASSES[ptype]
        instance = cls(phase_cfg)

        print(f"\n{'#'*70}")
        print(f"# PHASE {idx+1}/{len(phases)} — {ptype.upper()}")
        print(f"{'#'*70}")

        summary = instance.run(
            execute_episode=execute_episode,
            register_capability_summary=register_capability_summary,
            test_id=test_id,
            stage_name=stage.name,
        )
        phase_summaries.append(summary)

        print(f"\n{'#'*70}")
        print(f"# PHASE {idx+1}/{len(phases)} ({ptype.upper()}) COMPLETE")
        print(f"{'#'*70}")

    tool_name = register_capability_summary(
        test_id=test_id,
        max_verified=1,
        boundary=1,
        reason="multistage_test_complete",
    )

    return {
        "continue_training": False,
        "stop_reason": f"{stage.name}MultiStageComplete",
        "summary": {
            "enabled": True,
            "test_id": test_id,
            "status": "completed",
            "contract": contract_path,
            "phases": phase_summaries,
            "tool_name": tool_name,
        },
    }


def _normalize_phases(phases_cfg: Any) -> list[dict[str, Any]]:
    """Parse the phases list from test_specific config."""
    phases: list[dict[str, Any]] = []
    if not isinstance(phases_cfg, list):
        return phases
    for item in phases_cfg:
        if not isinstance(item, dict):
            continue
        ptype = str(item.get("type", "")).strip().lower()
        if ptype not in _PHASE_CLASSES:
            continue
        phases.append(dict(item))
    return phases
