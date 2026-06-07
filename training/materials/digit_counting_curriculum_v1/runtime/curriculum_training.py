"""Progressive curriculum section — gates upward through difficulty using RLHF."""

from __future__ import annotations

from collections import deque
from typing import Any, Callable

from src.models import EpisodeRecord
from src.training_type import _to_int, _to_float


class CurriculumTraining:
    """Progressive curriculum: escalates difficulty until the model hits its boundary."""

    def __init__(self, section_cfg: dict[str, Any]) -> None:
        self._min_level = _to_int(section_cfg, "min_level", 1)
        self._max_level = _to_int(section_cfg, "max_level", 20)
        self._max_total_samples = _to_int(section_cfg, "max_total_samples", 3000)
        self._gate_window_size = _to_int(section_cfg, "gate_window", 10)
        self._target_confidence = _to_float(section_cfg, "target_confidence", 1.0)
        self._tolerance = _to_float(section_cfg, "tolerance", 0.0)
        self._base_target_loops = _to_int(section_cfg, "base_target_loops", 40)
        self._max_loops_per_level = _to_int(section_cfg, "max_loops_per_level", 200)
        self._confidence_pressure_strength = _to_float(
            section_cfg, "confidence_pressure_strength", 0.5
        )
        self._report_interval = _to_int(section_cfg, "report_interval", 100)

    @staticmethod
    def _gate_hit(record, target_confidence: float, tolerance: float) -> bool:
        confidence_ok = abs(float(record.confidence) - target_confidence) <= tolerance
        return bool(record.success) and confidence_ok

    def run(
        self,
        *,
        execute_episode: Callable[..., EpisodeRecord],
        register_capability_summary: Callable[..., str],
        test_id: str,
        stage_name: str,
    ) -> dict[str, Any]:
        level = self._min_level
        level_loops = 0
        total_samples = 0
        best_verified = 0
        gate_window = deque(maxlen=max(1, self._gate_window_size))
        level_trends: list[dict[str, Any]] = []

        print(f"\n{'='*70}")
        print(f"CURRICULUM (RLHF)  levels {self._min_level}→{self._max_level}")
        print(f"{'='*70}")
        print(f"  Gate: {self._gate_window_size}  max/level: {self._max_loops_per_level}  budget: {self._max_total_samples}")
        print(f"{'─'*70}")

        while level <= self._max_level and total_samples < self._max_total_samples:
            target_loops = max(1, self._base_target_loops * level)
            progress_ratio = min(1.0, level_loops / target_loops)

            record = execute_episode(
                difficulty=level,
                progress_ratio=progress_ratio,
                confidence_pressure_strength=self._confidence_pressure_strength,
                training_mode="rlhf",
            )

            level_loops += 1
            total_samples += 1
            gate_window.append(
                self._gate_hit(record, self._target_confidence, self._tolerance)
            )

            if level_loops % self._report_interval == 0:
                level_trends.append({
                    "level": level,
                    "episode_at_level": level_loops,
                    "total_samples": total_samples,
                })

            if (
                len(gate_window) == gate_window.maxlen
                and all(gate_window)
            ):
                best_verified = level
                print(f"  >> Level {level} passed!  → level {level+1}  (samples: {total_samples})")
                if level >= self._max_level:
                    stop_reason = f"{stage_name}RequirementReached@{level}Digits"
                    tool_name = register_capability_summary(
                        test_id=test_id,
                        max_verified=best_verified,
                        boundary=None,
                        reason="max_requirement_reached",
                    )
                    return self._result(
                        "stopped_requirement_reached", best_verified, None,
                        total_samples, stop_reason, tool_name, level_trends,
                    )

                level += 1
                level_loops = 0
                gate_window.clear()
                continue

            if level_loops >= self._max_loops_per_level:
                print(f"  >> BOUNDARY at level {level}: max episodes exhausted (best: {best_verified})")
                stop_reason = f"{stage_name}CapabilityBoundary@{level}Digits"
                tool_name = register_capability_summary(
                    test_id=test_id,
                    max_verified=best_verified,
                    boundary=level,
                    reason="capability_boundary_reached_nonpass",
                )
                return self._result(
                    "stopped_capability_boundary", best_verified, level,
                    total_samples, stop_reason, tool_name, level_trends,
                )

        stop_reason = f"{stage_name}SampleBudgetReached@{level}Digits"
        tool_name = register_capability_summary(
            test_id=test_id,
            max_verified=best_verified,
            boundary=level,
            reason="sample_budget_reached",
        )
        return self._result(
            "stopped_sample_budget", best_verified, level,
            total_samples, stop_reason, tool_name, level_trends,
        )

    def _result(
        self,
        status: str,
        max_verified: int,
        boundary: int | None,
        samples: int,
        stop_reason: str,
        tool_name: str,
        level_trends: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "phase_type": "curriculum",
            "status": status,
            "max_verified_digits": max_verified,
            "boundary_digits": boundary,
            "samples": samples,
            "stop_reason": stop_reason,
            "tool_name": tool_name,
            "level_trends": level_trends,
        }
