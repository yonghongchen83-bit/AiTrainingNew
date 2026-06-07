from __future__ import annotations

from collections import deque
from typing import Any, Callable


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


def _to_int(cfg: dict[str, Any], key: str, default: int) -> int:
    return int(cfg.get(key, default))


def _to_float(cfg: dict[str, Any], key: str, default: float) -> float:
    return float(cfg.get(key, default))


def _gate_hit(record, target_confidence: float, tolerance: float) -> bool:
    confidence_ok = abs(float(record.confidence) - target_confidence) <= tolerance
    return bool(record.success) and confidence_ok


def _to_training_mode(value: Any, default: str = "rlhf") -> str:
    mode = str(value).strip().lower() if value is not None else default
    return mode if mode in ("rlhf", "sft") else default


def _normalize_training_schedule(schedule_cfg: Any, max_level: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not isinstance(schedule_cfg, list):
        return entries

    for item in schedule_cfg:
        if not isinstance(item, dict):
            continue

        mode = _to_training_mode(item.get("mode", "rlhf"))
        episodes = _to_int(item, "episodes", 0)
        if episodes <= 0:
            continue

        if "level" in item:
            min_level = max_level = int(item["level"])
        else:
            min_level = _to_int(item, "min_level", 1) if "min_level" in item else 1
            max_level = _to_int(item, "max_level", max_level) if "max_level" in item else max_level

        if min_level > max_level:
            min_level, max_level = max_level, min_level

        entries.append(
            {
                "mode": mode,
                "min_level": min_level,
                "max_level": max_level,
                "remaining": episodes,
            }
        )

    return entries


def _select_training_mode(level: int, schedule: list[dict[str, Any]], default_mode: str) -> str:
    for entry in schedule:
        if entry["remaining"] <= 0:
            continue
        if entry["min_level"] <= level <= entry["max_level"]:
            entry["remaining"] -= 1
            return entry["mode"]
    return default_mode


def _normalize_phases(phases_cfg: Any) -> list[dict[str, Any]]:
    phases: list[dict[str, Any]] = []
    if not isinstance(phases_cfg, list):
        return phases

    for item in phases_cfg:
        if not isinstance(item, dict):
            continue
        phase_type = str(item.get("type", "")).strip().lower()
        if phase_type not in {"sft", "trend", "curriculum", "sft_warmup", "legacy"}:
            continue
        phase = dict(item)
        phase["type"] = "sft" if phase_type == "sft_warmup" else phase_type
        phases.append(phase)

    return phases


def _run_sft_phase(
    phase_cfg: dict[str, Any],
    execute_episode: Callable[..., Any],
) -> dict[str, Any]:
    episodes = _to_int(phase_cfg, "episodes", 10)
    level = _to_int(phase_cfg, "level", 1)
    confidence_pressure_strength = _to_float(phase_cfg, "confidence_pressure_strength", 0.5)

    success_count = 0
    for episode in range(1, episodes + 1):
        progress_ratio = episode / max(1, episodes)
        record = execute_episode(
            difficulty=level,
            progress_ratio=progress_ratio,
            confidence_pressure_strength=confidence_pressure_strength,
            training_mode="sft",
        )
        if bool(record.success):
            success_count += 1

    return {
        "phase_type": "sft",
        "level": level,
        "episodes": episodes,
        "success_count": success_count,
        "accuracy": round(success_count / max(1, episodes), 4),
    }


def _run_curriculum_phase(
    phase_cfg: dict[str, Any],
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
    test_id: str,
    stage_name: str,
) -> dict[str, Any]:
    """Progressive curriculum — gates upward through difficulty levels using RLHF.
    Discovers the model's capability boundary and reports trend data at each level."""
    min_level = _to_int(phase_cfg, "min_level", 1)
    max_level = _to_int(phase_cfg, "max_level", 20)
    max_total_samples = _to_int(phase_cfg, "max_total_samples", 3000)
    gate_window_size = _to_int(phase_cfg, "gate_window", 10)
    target_confidence = _to_float(phase_cfg, "target_confidence", 1.0)
    tolerance = _to_float(phase_cfg, "tolerance", 0.0)
    base_target_loops = _to_int(phase_cfg, "base_target_loops", 40)
    max_loops_per_level = _to_int(phase_cfg, "max_loops_per_level", 200)
    confidence_pressure_strength = _to_float(phase_cfg, "confidence_pressure_strength", 0.5)
    report_interval = _to_int(phase_cfg, "report_interval", 100)

    level = min_level
    level_loops = 0
    total_samples = 0
    best_verified = 0
    gate_window = deque(maxlen=max(1, gate_window_size))

    # Track per-level trend snapshots
    level_trends: list[dict[str, Any]] = []

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

        # Snapshot at report intervals within each level
        if level_loops % report_interval == 0:
            level_trends.append({
                "level": level,
                "episode_at_level": level_loops,
                "total_samples": total_samples,
            })

        if len(gate_window) == gate_window.maxlen and all(gate_window):
            best_verified = level
            if level >= max_level:
                stop_reason = f"{stage_name}RequirementReached@{level}Digits"
                tool_name = register_capability_summary(
                    test_id=test_id,
                    max_verified=best_verified,
                    boundary=None,
                    reason="max_requirement_reached",
                )
                return {
                    "phase_type": "curriculum",
                    "status": "stopped_requirement_reached",
                    "max_verified_digits": best_verified,
                    "boundary_digits": None,
                    "samples": total_samples,
                    "stop_reason": stop_reason,
                    "tool_name": tool_name,
                    "level_trends": level_trends,
                }

            level += 1
            level_loops = 0
            gate_window.clear()
            continue

        if level_loops >= max_loops_per_level:
            stop_reason = f"{stage_name}CapabilityBoundary@{level}Digits"
            tool_name = register_capability_summary(
                test_id=test_id,
                max_verified=best_verified,
                boundary=level,
                reason="capability_boundary_reached_nonpass",
            )
            return {
                "phase_type": "curriculum",
                "status": "stopped_capability_boundary",
                "max_verified_digits": best_verified,
                "boundary_digits": level,
                "samples": total_samples,
                "stop_reason": stop_reason,
                "tool_name": tool_name,
                "level_trends": level_trends,
            }

    stop_reason = f"{stage_name}SampleBudgetReached@{level}Digits"
    tool_name = register_capability_summary(
        test_id=test_id,
        max_verified=best_verified,
        boundary=level,
        reason="sample_budget_reached",
    )
    return {
        "phase_type": "curriculum",
        "status": "stopped_sample_budget",
        "max_verified_digits": best_verified,
        "boundary_digits": level,
        "samples": total_samples,
        "stop_reason": stop_reason,
        "tool_name": tool_name,
        "level_trends": level_trends,
    }


def _run_staged_test(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    test_id = str(contract.get("test_id", "digit_counting"))
    specific_cfg = dict(DEFAULT_SPECIFIC)
    specific_cfg.update(contract.get("test_specific", {}))

    phases = _normalize_phases(specific_cfg.get("phases", []))
    if not phases:
        return run_test_loop(
            stage=stage,
            contract=contract,
            contract_path=contract_path,
            execute_episode=execute_episode,
            register_capability_summary=register_capability_summary,
        )

    phase_summaries: list[dict[str, Any]] = []
    for phase in phases:
        if phase["type"] == "sft":
            phase_summaries.append(_run_sft_phase(phase, execute_episode))
        elif phase["type"] == "curriculum":
            phase_summaries.append(_run_curriculum_phase(
                phase, execute_episode, register_capability_summary, test_id, stage.name,
            ))

    tool_name = register_capability_summary(
        test_id=test_id,
        max_verified=1,
        boundary=1,
        reason="multistage_test_complete",
    )

    summary = {
        "enabled": True,
        "test_id": test_id,
        "status": "completed",
        "contract": contract_path,
        "phases": phase_summaries,
        "tool_name": tool_name,
    }

    return {
        "continue_training": False,
        "stop_reason": f"{stage.name}MultiStageComplete",
        "summary": summary,
    }


def run_test_loop(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    test_id = str(contract.get("test_id", "digit_counting"))

    generic_cfg = dict(DEFAULT_GENERIC)
    generic_cfg.update(contract.get("generic", {}))

    specific_cfg = dict(DEFAULT_SPECIFIC)
    specific_cfg.update(contract.get("test_specific", {}))

    phases = _normalize_phases(specific_cfg.get("phases", []))
    if phases:
        return _run_staged_test(
            stage=stage,
            contract=contract,
            contract_path=contract_path,
            execute_episode=execute_episode,
            register_capability_summary=register_capability_summary,
        )

    level = _to_int(generic_cfg, "min_level", 1)
    max_level = _to_int(generic_cfg, "max_level", 20)
    max_total_samples = _to_int(generic_cfg, "max_total_samples", 3000)

    gate_window_size = _to_int(specific_cfg, "gate_window", 10)
    target_confidence = _to_float(specific_cfg, "target_confidence", 1.0)
    tolerance = _to_float(specific_cfg, "tolerance", 0.0)
    base_target_loops = _to_int(specific_cfg, "base_target_loops", 40)
    max_loops_per_level = _to_int(specific_cfg, "max_loops_per_level", 200)
    confidence_pressure_strength = _to_float(specific_cfg, "confidence_pressure_strength", 0.5)
    default_training_mode = _to_training_mode(specific_cfg.get("default_training_mode", "rlhf"))
    training_mode_schedule = _normalize_training_schedule(
        specific_cfg.get("training_mode_schedule", []),
        max_level=max_level,
    )

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
        episode_training_mode = _select_training_mode(
            level=level,
            schedule=training_mode_schedule,
            default_mode=default_training_mode,
        )

        record = execute_episode(
            difficulty=level,
            progress_ratio=progress_ratio,
            confidence_pressure_strength=confidence_pressure_strength,
            training_mode=episode_training_mode,
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
