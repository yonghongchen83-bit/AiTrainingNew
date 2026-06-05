from __future__ import annotations

from dataclasses import dataclass
from math import exp, log

from .agent import HeuristicLLMAgent
from .environment import MathEnvironment
from .models import EpisodeRecord, FailureType, GeneratedTask, Mode, RuntimeStats, StageConfig, StageMetrics
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


class ClosedLoopTrainer:
    def __init__(self, config: TrainerConfig) -> None:
        self.config = config
        self.toolbox = Toolbox()
        self.agent = HeuristicLLMAgent(seed=config.seed)

        self.stages = [
            StageConfig(0, "PlaceValue", False, None, False, False),
            StageConfig(1, "DigitCounting", False, None, False, False),
            StageConfig(2, "Addition1Digit", False, None, False, False),
        ]

        self.stats = RuntimeStats()

    def run(self) -> dict[str, object]:
        records: list[EpisodeRecord] = []
        per_stage = max(1, self.config.episodes // len(self.stages))

        for stage in self.stages:
            self._run_stage(stage=stage, episodes=per_stage, records=records)

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
        return summary

    def _run_stage(self, stage: StageConfig, episodes: int, records: list[EpisodeRecord]) -> None:
        env = MathEnvironment(stage=stage, seed=self.config.seed + stage.index)
        if stage.name not in self.stats.stage_metrics:
            self.stats.stage_metrics[stage.name] = StageMetrics()

        for _ in range(episodes):
            problem = env.reset()
            out = self.agent.predict(
                question=problem.question,
                expected_answer=problem.expected_answer,
                budget=env.budget,
                mode=self.config.mode,
                stage=stage,
            )

            if out.use_tool:
                self.toolbox.use_tool(out.tool_trigger)

            reward, success, actual_cost = env.step(
                out=out,
                expected_answer=problem.expected_answer,
                recursion_depth=1 if out.recursion_flag else 0,
            )
            self.agent.train_step(reward)

            surprise = abs(out.confidence - (1.0 if success else 0.0))
            failure_type = FailureType.NONE
            if env.budget <= 0:
                failure_type = FailureType.BUDGET_EXHAUSTED
            elif not success and out.confidence > 0.8:
                failure_type = FailureType.VALIDATION_FAILED

            if success and out.confidence > 0.9:
                self.toolbox.register("高信心模板", "在高置信成功情形下可复用的步骤模板")

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
                recursion_flag=out.recursion_flag,
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
