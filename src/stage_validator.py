from __future__ import annotations

import random
from dataclasses import dataclass

from .models import LLMOutput, StageConfig


@dataclass
class MathProblem:
    question: str
    expected_answer: str


class StageValidator:
    """Default answer checking and reward computation for a test stage.
    
    Tests MUST subclass this and override generate_problem() at minimum.
    Place the subclass in training/materials/<test>/runtime/stage_validator.py
    and it will be auto-discovered.
    """

    def generate_problem(self, difficulty: int | None, stage: StageConfig, rng: random.Random) -> MathProblem:
        """Generate a question. MUST be overridden by the test."""
        raise NotImplementedError(
            f"StageValidator.generate_problem() not implemented for stage '{stage.name}'. "
            "Test must provide a StageValidator subclass with generate_problem()."
        )

    def check_answer(self, question: str, answer: str, expected: str) -> bool:
        """Determine if the model's answer is correct. Override for fuzzy matching, etc."""
        return answer.strip() == expected

    def compute_reward(
        self,
        out: LLMOutput,
        success: bool,
        actual_cost: float,
        stage: StageConfig,
        progress_ratio: float = 0.0,
        confidence_pressure_strength: float = 0.0,
    ) -> float:
        """Default reward function. Override for custom reward formulas."""
        from .reward import compute_reward
        return compute_reward(
            out=out,
            success=success,
            actual_cost=actual_cost,
            stage=stage,
            progress_ratio=progress_ratio,
            confidence_pressure_strength=confidence_pressure_strength,
        )
