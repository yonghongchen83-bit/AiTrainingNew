from __future__ import annotations

import random
from dataclasses import dataclass

from .models import LLMOutput, StageConfig
from .reward import compute_reward


@dataclass
class MathProblem:
    question: str
    expected_answer: str


class MathEnvironment:
    def __init__(self, stage: StageConfig, seed: int = 7, initial_budget: float = 100.0) -> None:
        self.stage = stage
        self._rng = random.Random(seed)
        self.initial_budget = initial_budget
        self.budget = self.initial_budget

    def reset(self) -> MathProblem:
        self.budget = self.initial_budget
        return self._generate_problem()

    def _generate_problem(self) -> MathProblem:
        if self.stage.name == "PlaceValue":
            n = self._rng.randint(10, 999)
            place = self._rng.choice(["个位", "十位", "百位"])
            if place == "个位":
                expected = n % 10
            elif place == "十位":
                expected = (n // 10) % 10
            else:
                expected = (n // 100) % 10
            return MathProblem(
                question=f"数字 {n} 的{place}是几？",
                expected_answer=str(expected),
            )

        if self.stage.name == "DigitCounting":
            n = self._rng.randint(0, 99999)
            return MathProblem(
                question=f"数字 {n} 一共有几位？",
                expected_answer=str(len(str(n))),
            )

        # Stage 2 in this implementation: Addition1Digit
        a = self._rng.randint(0, 9)
        b = self._rng.randint(0, 9)
        return MathProblem(
            question=f"{a} + {b} = ?",
            expected_answer=str(a + b),
        )

    def step(self, out: LLMOutput, expected_answer: str, recursion_depth: int) -> tuple[float, bool, float]:
        success = out.answer.strip() == expected_answer
        actual_cost = 1.0 + (len(out.answer) / 10.0) + (recursion_depth * 2.0)
        reward = compute_reward(out=out, success=success, actual_cost=actual_cost, stage=self.stage)
        self.budget -= actual_cost
        return reward, success, actual_cost
