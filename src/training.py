from __future__ import annotations

import importlib.util
import json
import uuid
from dataclasses import dataclass, field
from math import exp, log
from pathlib import Path
from typing import Any

from .environment import MathEnvironment
from .llm_provider import LLMProvider, build_llm_provider
from .models import (
    EpisodeRecord,
    FailureType,
    FallbackEvent,
    GeneratedTask,
    LLMProviderType,
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
    llm_provider_type: LLMProviderType = LLMProviderType.SIMULATED
    llm_model_name: str | None = None
    max_recursion_depth: int = 2
    stage_initial_budget: float = 100.0
    convergence_window: int = 20
    convergence_success: float = 0.9
    convergence_surprise: float = 0.12
    stage_test_roots: dict[str, str] = field(default_factory=dict)


class ClosedLoopTrainer:
    def __init__(self, config: TrainerConfig) -> None:
        self.config = config
        self.toolbox = Toolbox()
        self.llm: LLMProvider = build_llm_provider(
            provider_type=config.llm_provider_type,
            seed=config.seed,
            simulation_mode=config.simulation_mode,
            model_name=config.llm_model_name,
        )

        self.stages = [
            StageConfig(0, "PlaceValue", False, None, False, False),
            StageConfig(1, "DigitCounting", False, None, False, False),
            StageConfig(2, "Addition1Digit", False, None, False, False),
        ]

        self.stats = RuntimeStats()
        self.tool_invocations: list[OpenAIToolCall] = []
        self.fallback_events: list[FallbackEvent] = []
        self.stop_reason: str = "Completed"
        self.stage_test_packages: dict[str, dict[str, Any]] = {
            stage_name: self._load_stage_test_package(test_root)
            for stage_name, test_root in self.config.stage_test_roots.items()
        }

        self.stage_test_summaries: dict[str, dict[str, Any]] = {
            stage_name: {
                "enabled": True,
                "test_id": package["test_id"],
                "status": "not_run",
                "contract": package["contract_relpath"],
                "max_verified_digits": 0,
                "boundary_digits": None,
                "samples": 0,
                "stop_reason": None,
                "tool_name": None,
            }
            for stage_name, package in self.stage_test_packages.items()
        }

    def _import_function(self, module_path: Path, function_name: str):
        spec = importlib.util.spec_from_file_location(f"test_runtime_{module_path.stem}", module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load test runtime module from: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, function_name, None)
        if fn is None:
            raise RuntimeError(f"Function '{function_name}' not found in module: {module_path}")
        return fn

    def _load_stage_test_package(self, test_root_ref: str) -> dict[str, Any]:
        repo_root = Path(__file__).resolve().parent.parent
        test_root = Path(test_root_ref)
        if not test_root.is_absolute():
            test_root = repo_root / test_root

        contract_path = test_root / "config" / "test_contract.json"
        if not contract_path.exists():
            raise RuntimeError(f"Missing test contract: {contract_path}")

        payload = json.loads(contract_path.read_text(encoding="utf-8"))
        test_id = payload.get("test_id")
        if not isinstance(test_id, str) or not test_id:
            raise RuntimeError("test_contract.json must define non-empty string field: test_id")

        controller_cfg = payload.get("controller", {})
        if not isinstance(controller_cfg, dict):
            raise RuntimeError("test_contract.json field 'controller' must be an object")

        module_ref = controller_cfg.get("module")
        if module_ref is None:
            module_path = test_root / "runtime" / "controller.py"
        else:
            module_path = Path(str(module_ref))
            if not module_path.is_absolute():
                module_path = repo_root / module_path

        entry_name = str(controller_cfg.get("entry", "run_test_loop"))
        controller = self._import_function(module_path, entry_name)

        return {
            "test_id": test_id,
            "test_root": test_root,
            "contract_path": contract_path,
            "contract_relpath": str(contract_path.relative_to(repo_root)),
            "contract": payload,
            "controller": controller,
        }

    def run(self) -> dict[str, object]:
        records: list[EpisodeRecord] = []
        per_stage = max(1, self.config.episodes // len(self.stages))

        for idx, stage in enumerate(self.stages):
            should_continue = self._run_stage(stage=stage, episodes=per_stage, records=records)
            if not should_continue:
                break

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
        summary["stage_tests"] = self.stage_test_summaries
        summary["llm_provider"] = {
            "type": self.llm.provider_type,
            "model": self.llm.model_name,
        }
        return summary

    def _run_stage(self, stage: StageConfig, episodes: int, records: list[EpisodeRecord]) -> bool:
        env = MathEnvironment(
            stage=stage,
            seed=self.config.seed + stage.index,
            initial_budget=self.config.stage_initial_budget,
        )
        if stage.name not in self.stats.stage_metrics:
            self.stats.stage_metrics[stage.name] = StageMetrics()

        package = self.stage_test_packages.get(stage.name)
        if package is not None:
            return self._run_stage_test_controller(stage=stage, env=env, records=records, package=package)

        for _ in range(episodes):
            self._execute_stage_episode(stage=stage, env=env, records=records)

        return True

    def _run_stage_test_controller(
        self,
        stage: StageConfig,
        env: MathEnvironment,
        records: list[EpisodeRecord],
        package: dict[str, Any],
    ) -> bool:
        controller = package["controller"]

        def execute_episode(
            *,
            difficulty: int | None = None,
            progress_ratio: float = 0.0,
            confidence_pressure_strength: float = 0.0,
        ) -> EpisodeRecord:
            return self._execute_stage_episode(
                stage=stage,
                env=env,
                records=records,
                difficulty=difficulty,
                progress_ratio=progress_ratio,
                confidence_pressure_strength=confidence_pressure_strength,
            )

        def register_capability_summary(
            *,
            test_id: str,
            max_verified: int,
            boundary: int | None,
            reason: str,
            capability: str | None = None,
        ) -> str:
            return self._register_test_capability_summary(
                test_id=test_id,
                max_verified=max_verified,
                boundary=boundary,
                reason=reason,
                capability=capability,
            )

        result = controller(
            stage=stage,
            contract=package["contract"],
            contract_path=package["contract_relpath"],
            execute_episode=execute_episode,
            register_capability_summary=register_capability_summary,
        )
        if not isinstance(result, dict):
            raise RuntimeError("Test controller must return a dict result")

        stop_reason = result.get("stop_reason")
        if isinstance(stop_reason, str) and stop_reason:
            self.stop_reason = stop_reason

        summary = result.get("summary")
        if isinstance(summary, dict):
            self.stage_test_summaries[stage.name] = summary

        continue_training = result.get("continue_training")
        if isinstance(continue_training, bool):
            return continue_training

        return False

    def _execute_stage_episode(
        self,
        stage: StageConfig,
        env: MathEnvironment,
        records: list[EpisodeRecord],
        difficulty: int | None = None,
        progress_ratio: float = 0.0,
        confidence_pressure_strength: float = 0.0,
    ) -> EpisodeRecord:
        problem = env.reset(difficulty=difficulty)
        recursion_depth = 0
        out = self.llm.predict(
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
                can_attempt = self.config.simulation_mode == SimulationMode.IMPROVING and out.confidence >= min_attempt_conf
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
                return record

            recursion_depth += 1
            child_budget = env.budget * 0.8
            out = self.llm.predict(
                question=problem.question,
                expected_answer=problem.expected_answer,
                budget=child_budget,
                mode=self.config.mode,
                stage=stage,
            )

        if out.use_tool:
            self.toolbox.use_tool(out.tool_trigger)

        reward, success, actual_cost = env.step(
            out=out,
            expected_answer=problem.expected_answer,
            recursion_depth=recursion_depth,
            progress_ratio=progress_ratio,
            confidence_pressure_strength=confidence_pressure_strength,
        )
        self.llm.train_step(reward)

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
        return record

    def _register_test_capability_summary(
        self,
        test_id: str,
        max_verified: int,
        boundary: int | None,
        reason: str,
        capability: str | None = None,
    ) -> str:
        tool_name = f"{''.join(part.capitalize() for part in test_id.split('_'))}Capability"
        boundary_text = str(boundary) if boundary is not None else "none"
        description = (
            f"{test_id} capability summary: "
            f"max_verified={max_verified}, boundary={boundary_text}, reason={reason}"
        )
        capability_name = capability or f"meta_capability.{test_id}"
        self.toolbox.register(
            trigger_words=[tool_name, f"{test_id}_capability"],
            description=description,
            name=tool_name,
            capability=capability_name,
        )
        return tool_name

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
            out = self.llm.predict(
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
            self.llm.train_step(reward)

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
            adaptive = base - (0.25 - 0.15 * self.llm.learning_progress())
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
