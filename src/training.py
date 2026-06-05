from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from math import exp, log
from typing import Any

from .agent import HeuristicLLMAgent
from .environment import MathEnvironment
from .models import (
    EpisodeRecord,
    FailureType,
    FallbackEvent,
    GeneratedTask,
    Mode,
    OpenAIFunction,
    OpenAIToolCall,
    RuntimeStats,
    SimulationMode,
    StageConfig,
    StageMetrics,
)
from .reward import compute_reward_profile
from .self_extension import SelfExtensionPlanner
from .toolbox import Toolbox


@dataclass
class TrainerConfig:
    episodes: int = 120
    mode: Mode = Mode.EXPERT
    seed: int = 11
    enable_self_extension: bool = True
    self_task_count: int = 60
    simulation_mode: SimulationMode = SimulationMode.IMPROVING
    max_recursion_depth: int = 2
    stage_initial_budget: float = 100.0
    convergence_window: int = 20
    convergence_success: float = 0.9
    convergence_surprise: float = 0.12


class ClosedLoopTrainer:
    def __init__(self, config: TrainerConfig) -> None:
        self.config = config
        self.toolbox = Toolbox()
        self.agent = HeuristicLLMAgent(seed=config.seed, simulation_mode=config.simulation_mode)

        self.stages = [
            StageConfig(0, "PlaceValue", False, None, False, False),
            StageConfig(1, "DigitCounting", False, None, False, False),
            StageConfig(2, "Addition1Digit", False, None, False, False),
        ]

        self.stats = RuntimeStats()
        self.tool_invocations: list[OpenAIToolCall] = []
        self.fallback_events: list[FallbackEvent] = []
        self.stop_reason: str = "Completed"

    def run(self) -> dict[str, object]:
        records: list[EpisodeRecord] = []
        per_stage = max(1, self.config.episodes // len(self.stages))

        for idx, stage in enumerate(self.stages):
            self._run_stage(stage=stage, episodes=per_stage, records=records)
            if self._is_naturally_converged(records) and self.config.simulation_mode == SimulationMode.IMPROVING:
                self.stop_reason = f"NaturalConvergence@{stage.name}"
                # 达到自然收敛后提前结束主循环。
                if idx < len(self.stages) - 1:
                    break

        self_extension_summary: dict[str, object] = {
            "enabled": self.config.enable_self_extension,
            "generated_tasks": 0,
            "added_tools": [],
            "expanded_stages": [],
        }

        if self.config.enable_self_extension:
            planner = SelfExtensionPlanner(seed=self.config.seed + 100)
            generated_tasks = planner.generate_tasks(count=self.config.self_task_count)
            base_cal_error = self._build_summary(records)["calibration_error"]
            reward_profile = planner.generate_reward_functions(calibration_error=float(base_cal_error))
            new_stages = planner.expand_curriculum(base_stages=self.stages)
            added_tools = planner.build_toolbox(toolbox=self.toolbox, tasks=generated_tasks)

            for stage in new_stages:
                stage_tasks = [t for t in generated_tasks if t.stage_name == stage.name]
                self._run_generated_stage(stage=stage, tasks=stage_tasks, records=records, profile=reward_profile)

            self_extension_summary = {
                "enabled": True,
                "generated_tasks": len(generated_tasks),
                "added_tools": added_tools,
                "expanded_stages": [s.name for s in new_stages],
                "surprise_weight": reward_profile.penalize_surprise_weight,
            }

        summary = self._build_summary(records)
        summary["self_extension"] = self_extension_summary
        summary["tool_invocations"] = [
            {
                "id": c.id,
                "type": c.type,
                "function": {
                    "name": c.function.name,
                    "arguments": c.function.arguments,
                },
            }
            for c in self.tool_invocations
        ]
        summary["fallback_events"] = [
            {
                "reason_code": e.reason_code,
                "reason": e.reason,
                "stage": e.stage,
                "task": e.task,
                "remaining_budget": round(e.remaining_budget, 4),
                "details": e.details,
            }
            for e in self.fallback_events
        ]
        summary["stop_reason"] = self.stop_reason
        summary["simulation_mode"] = self.config.simulation_mode.value
        return summary

    def _run_stage(self, stage: StageConfig, episodes: int, records: list[EpisodeRecord]) -> None:
        env = MathEnvironment(
            stage=stage,
            seed=self.config.seed + stage.index,
            initial_budget=self.config.stage_initial_budget,
        )
        if stage.name not in self.stats.stage_metrics:
            self.stats.stage_metrics[stage.name] = StageMetrics()

        for _ in range(episodes):
            problem = env.reset()
            recursion_depth = 0
            out = self.agent.predict(
                question=problem.question,
                expected_answer=problem.expected_answer,
                budget=env.budget,
                mode=self.config.mode,
                stage=stage,
            )

            threshold = self._threshold(self.config.mode)
            while out.confidence < threshold:
                if out.use_tool and out.tool_trigger and self.toolbox.has_tool(out.tool_trigger):
                    self.toolbox.use_tool(out.tool_trigger)
                    self._emit_tool_call(
                        "toolsApplication",
                        {
                            "tool": out.tool_trigger,
                            "stage": stage.name,
                            "task": problem.question,
                            "reason": "low_confidence_need_tool",
                        },
                    )
                    break

                if recursion_depth >= self.config.max_recursion_depth or env.budget * 0.8 <= 0:
                    # improving 分支允许在中等置信度下继续尝试，避免全量退化为失败回退。
                    min_attempt_conf = max(0.35, threshold - 0.25)
                    can_attempt = (
                        self.config.simulation_mode == SimulationMode.IMPROVING
                        and out.confidence >= min_attempt_conf
                    )
                    if can_attempt:
                        break

                    self._register_fallback(
                        stage=stage.name,
                        task=problem.question,
                        failure_type=FailureType.IRREDUCIBLE_UNCERTAINTY,
                        remaining_budget=env.budget,
                        reason="low_confidence_and_no_tool",
                        details={"confidence": round(out.confidence, 4), "threshold": threshold},
                    )
                    record = EpisodeRecord(
                        stage_name=stage.name,
                        question=problem.question,
                        answer=out.answer,
                        expected=problem.expected_answer,
                        success=False,
                        confidence=out.confidence,
                        surprise=abs(out.confidence - 0.0),
                        reward=-1.0,
                        cost=0.0,
                        used_tool=None,
                        recursion_flag=True,
                        background_locked=out.background_locked,
                        failure_type=FailureType.IRREDUCIBLE_UNCERTAINTY,
                    )
                    records.append(record)
                    self._accumulate(record)
                    out = None
                    break

                recursion_depth += 1
                child_budget = env.budget * 0.8
                out = self.agent.predict(
                    question=problem.question,
                    expected_answer=problem.expected_answer,
                    budget=child_budget,
                    mode=self.config.mode,
                    stage=stage,
                )

            if out is None:
                continue

            if out.use_tool:
                self.toolbox.use_tool(out.tool_trigger)

            reward, success, actual_cost = env.step(
                out=out,
                expected_answer=problem.expected_answer,
                recursion_depth=recursion_depth,
            )
            self.agent.train_step(reward)

            surprise = abs(out.confidence - (1.0 if success else 0.0))
            failure_type = FailureType.NONE
            if env.budget <= 0:
                failure_type = FailureType.BUDGET_EXHAUSTED
                self._register_fallback(
                    stage=stage.name,
                    task=problem.question,
                    failure_type=FailureType.BUDGET_EXHAUSTED,
                    remaining_budget=env.budget,
                    reason="remaining_budget<=0",
                    details={"actual_cost": round(actual_cost, 4)},
                )
            elif not success and out.confidence > 0.8:
                failure_type = FailureType.VALIDATION_FAILED

            if success and out.confidence > 0.9:
                self.toolbox.register(
                    trigger_words=["高信心模板", "HighConfidenceTemplate"],
                    description="在高置信成功情形下可复用的步骤模板",
                    name="HighConfidenceTemplate",
                )

            record = EpisodeRecord(
                stage_name=stage.name,
                question=problem.question,
                answer=out.answer,
                expected=problem.expected_answer,
                success=success,
                confidence=out.confidence,
                surprise=surprise,
                reward=reward,
                cost=actual_cost,
                used_tool=out.tool_trigger,
                recursion_flag=recursion_depth > 0,
                background_locked=out.background_locked,
                failure_type=failure_type,
            )
            records.append(record)
            self._accumulate(record)

    def _run_generated_stage(
        self,
        stage: StageConfig,
        tasks: list[GeneratedTask],
        records: list[EpisodeRecord],
        profile,
    ) -> None:
        if stage.name not in self.stats.stage_metrics:
            self.stats.stage_metrics[stage.name] = StageMetrics()

        for task in tasks:
            out = self.agent.predict(
                question=task.question,
                expected_answer=task.expected_answer,
                budget=100.0,
                mode=self.config.mode,
                stage=stage,
            )
            actual_cost = 1.0 + len(out.answer) / 10.0 + (2.0 if out.recursion_flag else 0.0)
            success = out.answer.strip() == task.expected_answer
            reward = compute_reward_profile(
                out=out,
                success=success,
                actual_cost=actual_cost,
                estimated_cost=out.estimated_cost,
                profile=profile,
            )
            self.agent.train_step(reward)

            if out.use_tool:
                self.toolbox.use_tool(out.tool_trigger)

            failure_type = FailureType.NONE
            if not success and out.confidence > 0.8:
                failure_type = FailureType.VALIDATION_FAILED

            record = EpisodeRecord(
                stage_name=stage.name,
                question=task.question,
                answer=out.answer,
                expected=task.expected_answer,
                success=success,
                confidence=out.confidence,
                surprise=abs(out.confidence - (1.0 if success else 0.0)),
                reward=reward,
                cost=actual_cost,
                used_tool=out.tool_trigger,
                recursion_flag=out.recursion_flag,
                background_locked=out.background_locked,
                failure_type=failure_type,
            )
            records.append(record)
            self._accumulate(record)

    def _accumulate(self, record: EpisodeRecord) -> None:
        self.stats.total_episodes += 1
        self.stats.total_reward += record.reward

        if (not record.success) and record.confidence > 0.8:
            self.stats.false_high_confidence += 1

        if record.cost > 0:
            ratio = record.cost / max(1.0, record.cost)
            self.stats.budget_efficiency_product *= ratio
            self.stats.budget_efficiency_count += 1

        m = self.stats.stage_metrics[record.stage_name]
        m.episodes += 1
        m.success_count += 1 if record.success else 0
        m.surprise_sum += record.surprise

    def _threshold(self, mode: Mode) -> float:
        if mode == Mode.CHAT:
            base = 0.4
        elif mode == Mode.EXPERT:
            base = 0.8
        else:
            base = 0.9

        if self.config.simulation_mode == SimulationMode.IMPROVING:
            # 改善模式需要可学习入口：初期降低门槛，随 skill 提升逐步恢复严格性。
            adaptive = base - (0.25 - 0.15 * self.agent.skill)
            return max(0.4, min(base, adaptive))

        return base

    def _emit_tool_call(self, name: str, arguments: dict[str, Any]) -> None:
        call = OpenAIToolCall(
            id=f"call_{uuid.uuid4().hex[:12]}",
            type="function",
            function=OpenAIFunction(name=name, arguments=json.dumps(arguments, ensure_ascii=False)),
        )
        self.tool_invocations.append(call)

    def _register_fallback(
        self,
        stage: str,
        task: str,
        failure_type: FailureType,
        remaining_budget: float,
        reason: str,
        details: dict[str, Any],
    ) -> None:
        event = FallbackEvent(
            reason_code=failure_type.value,
            reason=reason,
            stage=stage,
            task=task,
            remaining_budget=remaining_budget,
            details=details,
        )
        self.fallback_events.append(event)

        self._emit_tool_call(
            "CompletionFailed",
            {
                "reason_code": failure_type.value,
                "reason": reason,
                "stage": stage,
                "task": task,
                "remaining_budget": remaining_budget,
                "details": details,
            },
        )

        if failure_type == FailureType.IRREDUCIBLE_UNCERTAINTY:
            self._emit_tool_call(
                "TrainingRequired",
                {
                    "domain": "math",
                    "gap": "low_confidence_no_tool_path",
                    "sample_task": task,
                },
            )
            self._emit_tool_call(
                "ToolsExtension",
                {
                    "requested_tool": "expression_decompose",
                    "reason": "recursion_failed_no_tool",
                    "stage": stage,
                },
            )

    def _is_naturally_converged(self, records: list[EpisodeRecord]) -> bool:
        if self.config.simulation_mode != SimulationMode.IMPROVING:
            return False
        if len(records) < self.config.convergence_window:
            return False

        window = records[-self.config.convergence_window :]
        success_rate = sum(1 for r in window if r.success) / len(window)
        mean_surprise = sum(r.surprise for r in window) / len(window)
        return success_rate >= self.config.convergence_success and mean_surprise <= self.config.convergence_surprise

    def _build_summary(self, records: list[EpisodeRecord]) -> dict[str, object]:
        cal_error = 0.0
        if records:
            cal_error = sum(r.surprise for r in records) / len(records)

        efficiency_geo_mean = 1.0
        if self.stats.budget_efficiency_count > 0:
            efficiency_geo_mean = exp(
                log(self.stats.budget_efficiency_product) / self.stats.budget_efficiency_count
            )

        return {
            "episodes": self.stats.total_episodes,
            "total_reward": round(self.stats.total_reward, 4),
            "calibration_error": round(cal_error, 4),
            "false_high_confidence": self.stats.false_high_confidence,
            "budget_efficiency": round(efficiency_geo_mean, 4),
            "stage_metrics": {
                stage: {
                    "success_rate": round(metric.success_rate, 4),
                    "mean_surprise": round(metric.mean_surprise, 4),
                    "episodes": metric.episodes,
                }
                for stage, metric in self.stats.stage_metrics.items()
            },
            "records": records,
        }
