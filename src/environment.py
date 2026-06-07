from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from .models import LLMOutput, StageConfig
from .reward import compute_reward
from .stage_validator import MathProblem

SYSTEM_PROMPT_JSON = (
    "Return a JSON object with key: confidence (number 0 to 1)."
)


class MathEnvironment:
    def __init__(self, stage: StageConfig, seed: int = 7, initial_budget: float = 100.0,
                 system_prompt: str | None = None) -> None:
        self.stage = stage
        self._rng = random.Random(seed)
        self.initial_budget = initial_budget
        self.budget = self.initial_budget
        self.system_prompt = system_prompt or SYSTEM_PROMPT_JSON

    def reset(self, difficulty: int | None = None,
              problem_generator: Callable[[int | None, StageConfig, random.Random], MathProblem] | None = None) -> MathProblem:
        self.budget = self.initial_budget
        if problem_generator is None:
            raise RuntimeError("MathEnvironment.reset() requires a problem_generator from the test's StageValidator")
        return problem_generator(difficulty, self.stage, self._rng)

    def step(
        self,
        out: LLMOutput,
        expected_answer: str,
        recursion_depth: int,
        success: bool = False,
        progress_ratio: float = 0.0,
        confidence_pressure_strength: float = 0.0,
        reward: float | None = None,
    ) -> tuple[float, bool, float]:
        actual_cost = 1.0 + (len(expected_answer) / 10.0) + (recursion_depth * 2.0)
        if reward is None:
            reward = compute_reward(
                out=out,
                success=success,
                actual_cost=actual_cost,
                stage=self.stage,
                progress_ratio=progress_ratio,
                confidence_pressure_strength=confidence_pressure_strength,
            )
        self.budget -= actual_cost
        return reward, success, actual_cost
