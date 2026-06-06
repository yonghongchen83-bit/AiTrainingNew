"""
DigitCounting-specific fake LLM simulator.

This is the simulated LLM for the DigitCounting curriculum test.
It provides deterministic behavior to validate the framework's
capability-boundary detection across digit lengths.

Fixed profile:
  - <= 3 digits: 100% correct, confidence=1.0
  - 4 digits:    90% correct
  - >= 5 digits: 60% correct

Dumb mode: always wrong (for early-termination testing).
"""

from __future__ import annotations

import random

from src.models import LLMOutput, Mode, SimulationMode, StageConfig


class DigitCountingSimulationLLM:
    def __init__(self, seed: int = 101, simulation_mode: SimulationMode = SimulationMode.IMPROVING, dumb_mode: bool = False) -> None:
        self._rng = random.Random(seed)
        self.simulation_mode = simulation_mode
        self.dumb_mode = dumb_mode

    @property
    def provider_type(self) -> str:
        return "simulated"

    @property
    def model_name(self) -> str | None:
        return "digit_counting_simulator"

    def learning_progress(self) -> float:
        return 0.5

    def train_step(self, reward: float) -> None:
        _ = reward

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        _ = (question, budget, stage)

        # dumb mode: always wrong
        if self.dumb_mode:
            wrong = str(int(expected_answer) + 1) if expected_answer.isdigit() else "999"
            return LLMOutput(
                answer=wrong,
                confidence=0.15,
                estimated_cost=2,
                use_tool=False,
                tool_trigger=None,
                recursion_flag=True,
                background_locked=True,
                clarification="dumb_mode_active",
            )

        digits = int(expected_answer) if expected_answer.isdigit() else 1
        target_accuracy = self._accuracy_for_digits(digits)
        will_be_correct = self._rng.random() < target_accuracy

        if digits <= 3:
            confidence = 1.0
        elif digits == 4:
            confidence = 0.90 if will_be_correct else 0.7
        else:
            confidence = 0.70 if will_be_correct else 0.45

        answer = expected_answer if will_be_correct else self._perturb_answer(expected_answer)
        threshold = self._threshold(mode)

        return LLMOutput(
            answer=answer,
            confidence=confidence,
            estimated_cost=max(1, 1 + digits // 3),
            use_tool=False,
            tool_trigger=None,
            recursion_flag=confidence < threshold,
            background_locked=True,
            clarification=None,
        )

    @staticmethod
    def _accuracy_for_digits(digits: int) -> float:
        if digits <= 3:
            return 1.0
        if digits == 4:
            return 0.9
        return 0.6

    @staticmethod
    def _threshold(mode: Mode) -> float:
        if mode == Mode.CHAT:
            return 0.4
        if mode == Mode.EXPERT:
            return 0.8
        return 0.9

    def _perturb_answer(self, expected_answer: str) -> str:
        if expected_answer.isdigit():
            v = int(expected_answer)
            step = self._rng.choice([-1, 1])
            return str(max(1, v + step))
        return "1"


def create_simulator(seed: int = 101, dumb_mode: bool = False) -> DigitCountingSimulationLLM:
    """Factory function — called by the training pipeline to instantiate this test's simulator."""
    return DigitCountingSimulationLLM(seed=seed, simulation_mode=SimulationMode.IMPROVING, dumb_mode=dumb_mode)
