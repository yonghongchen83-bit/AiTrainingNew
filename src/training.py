from __future__ import annotations

from dataclasses import dataclass
from math import exp, log

from .agent import HeuristicLLMAgent
from .environment import MathEnvironment
from .models import EpisodeRecord, FailureType, Mode, RuntimeStats, StageConfig, StageMetrics
from .toolbox import Toolbox


@dataclass
class TrainerConfig:
    episodes: int = 120
    mode: Mode = Mode.EXPERT
    seed: int = 11


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
            env = MathEnvironment(stage=stage, seed=self.config.seed + stage.index)
            if stage.name not in self.stats.stage_metrics:
                self.stats.stage_metrics[stage.name] = StageMetrics()

            for _ in range(per_stage):
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

        return self._build_summary(records)

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
