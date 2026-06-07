"""Top-level test controller — dispatches phases to dedicated section classes."""

from __future__ import annotations

from collections import deque
from typing import Any, Callable

from training.materials.digit_counting_curriculum_v1.runtime.sft_training import SftTraining
from training.materials.digit_counting_curriculum_v1.runtime.curriculum_training import CurriculumTraining
from src.training_type import _to_int, _to_float


DEFAULT_GENERIC: dict[str, Any] = {
    "min_level": 1,
    "max_level": 20,
    "max_total_samples": 3000,
}

DEFAULT_SPECIFIC: dict[str, Any] = {
    "gate_window": 10,
    "target_confidence": 1.0,
    "tolerance": 0.0,
    "base_target_loops": 40,
    "max_loops_per_level": 200,
    "confidence_pressure_strength": 0.5,
}


# ── Phase dispatch registry ──────────────────────────────────────────

_PHASE_CLASSES: dict[str, type] = {
    "sft": SftTraining,
    "curriculum": CurriculumTraining,
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


def _gate_hit(record, target_confidence: float, tolerance: float) -> bool:
    """Check if a single episode clears the confidence+accuracy gate."""
    confidence_ok = abs(float(record.confidence) - target_confidence) <= tolerance
    return bool(record.success) and confidence_ok


def _run_phases(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    """Execute all phases defined in the contract, dispatching each to its class."""
    test_id = str(contract.get("test_id", "digit_counting"))
    specific_cfg = dict(DEFAULT_SPECIFIC)
    specific_cfg.update(contract.get("test_specific", {}))
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


# ── Legacy single-loop entry point (backward compatible) ─────────────

def run_test_loop(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    """Main entry point. If phases are defined, dispatches to _run_phases.
    Otherwise falls back to the original gate-loop (legacy behavior)."""
    specific_cfg = dict(DEFAULT_SPECIFIC)
    specific_cfg.update(contract.get("test_specific", {}))

    phases = _normalize_phases(specific_cfg.get("phases", []))
    if phases:
        return _run_phases(
            stage=stage,
            contract=contract,
            contract_path=contract_path,
            execute_episode=execute_episode,
            register_capability_summary=register_capability_summary,
        )

    # ── Legacy gate-loop below (unchanged) ────────────────────────────
    test_id = str(contract.get("test_id", "digit_counting"))
    generic_cfg = dict(DEFAULT_GENERIC)
    generic_cfg.update(contract.get("generic", {}))

    level = _to_int(generic_cfg, "min_level", 1)
    max_level = _to_int(generic_cfg, "max_level", 20)
    max_total_samples = _to_int(generic_cfg, "max_total_samples", 3000)

    gate_window_size = _to_int(specific_cfg, "gate_window", 10)
    target_confidence = _to_float(specific_cfg, "target_confidence", 1.0)
    tolerance = _to_float(specific_cfg, "tolerance", 0.0)
    base_target_loops = _to_int(specific_cfg, "base_target_loops", 40)
    max_loops_per_level = _to_int(specific_cfg, "max_loops_per_level", 200)
    confidence_pressure_strength = _to_float(specific_cfg, "confidence_pressure_strength", 0.5)

    best_verified = 0
    level_loops = 0
    total_samples = 0
    gate_window = deque(maxlen=max(1, gate_window_size))

    summary: dict[str, Any] = {
        "enabled": True,
        "test_id": test_id,
        "status": "running",
        "contract": contract_path,
        "max_verified_digits": 0,
        "boundary_digits": None,
        "samples": 0,
        "stop_reason": None,
        "tool_name": None,
    }

    while level <= max_level and total_samples < max_total_samples:
        target_loops = max(1, base_target_loops * level)
        progress_ratio = min(1.0, level_loops / target_loops)

        record = execute_episode(
            difficulty=level,
            progress_ratio=progress_ratio,
            confidence_pressure_strength=confidence_pressure_strength,
            training_mode="rlhf",
        )

        level_loops += 1
        total_samples += 1
        gate_window.append(_gate_hit(record, target_confidence=target_confidence, tolerance=tolerance))

        if len(gate_window) == gate_window.maxlen and all(gate_window):
            best_verified = level
            if level >= max_level:
                stop_reason = f"{stage.name}RequirementReached@{level}Digits"
                tool_name = register_capability_summary(
                    test_id=test_id,
                    max_verified=best_verified,
                    boundary=None,
                    reason="max_requirement_reached",
                )
                summary.update(
                    {
                        "status": "stopped_requirement_reached",
                        "max_verified_digits": best_verified,
                        "boundary_digits": None,
                        "samples": total_samples,
                        "stop_reason": stop_reason,
                        "tool_name": tool_name,
                    }
                )
                return {
                    "continue_training": False,
                    "stop_reason": stop_reason,
                    "summary": summary,
                }

            level += 1
            level_loops = 0
            gate_window.clear()
            continue

        if level_loops >= max_loops_per_level:
            stop_reason = f"{stage.name}CapabilityBoundary@{level}Digits"
            tool_name = register_capability_summary(
                test_id=test_id,
                max_verified=best_verified,
                boundary=level,
                reason="capability_boundary_reached_nonpass",
            )
            summary.update(
                {
                    "status": "stopped_capability_boundary",
                    "max_verified_digits": best_verified,
                    "boundary_digits": level,
                    "samples": total_samples,
                    "stop_reason": stop_reason,
                    "tool_name": tool_name,
                }
            )
            return {
                "continue_training": False,
                "stop_reason": stop_reason,
                "summary": summary,
            }

    stop_reason = f"{stage.name}SampleBudgetReached@{level}Digits"
    tool_name = register_capability_summary(
        test_id=test_id,
        max_verified=best_verified,
        boundary=level,
        reason="sample_budget_reached",
    )
    summary.update(
        {
            "status": "stopped_sample_budget",
            "max_verified_digits": best_verified,
            "boundary_digits": level,
            "samples": total_samples,
            "stop_reason": stop_reason,
            "tool_name": tool_name,
        }
    )
    return {
        "continue_training": False,
        "stop_reason": stop_reason,
        "summary": summary,
    }
