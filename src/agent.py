from __future__ import annotations

import random

from .models import LLMOutput, Mode, SimulationMode, StageConfig


class HeuristicLLMAgent:
    """
    可运行的闭环代理：
    - 以启发式生成 answer/confidence/cost/tool/recursion/background 字段
    - 根据 episode 进度逐步提高正确率，模拟训练改进
    """

    def __init__(self, seed: int = 13, simulation_mode: SimulationMode = SimulationMode.IMPROVING) -> None:
        self._rng = random.Random(seed)
        self.skill = 0.25
        self.simulation_mode = simulation_mode

    def train_step(self, reward: float) -> None:
        # improving 模式会学习；stuck 模式模拟难以学习/随机波动。
        if self.simulation_mode == SimulationMode.IMPROVING:
            delta = 0.01 if reward > 0 else -0.003
            self.skill = max(0.05, min(1.0, self.skill + delta))
            return

        jitter = self._rng.uniform(-0.01, 0.01)
        self.skill = max(0.05, min(0.25, self.skill + jitter))

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        threshold = self._threshold(mode)
        need_tool = stage.tool_required

        if self.simulation_mode == SimulationMode.IMPROVING:
            base_conf = 0.35 + self.skill * 0.6
            noise = self._rng.uniform(-0.08, 0.08)
            will_be_correct = self._rng.random() < self.skill
        else:
            base_conf = 0.18 + self.skill * 0.4
            noise = self._rng.uniform(-0.22, 0.22)
            will_be_correct = self._rng.random() < 0.12

        confidence = max(0.01, min(1.0, base_conf + noise))
        if self.simulation_mode == SimulationMode.IMPROVING and self.skill >= 0.985 and will_be_correct:
            confidence = 1.0
        answer = expected_answer if will_be_correct else self._perturb_answer(expected_answer)

        estimated_cost = max(1, int(1 + len(answer) / 3 + (0 if confidence > threshold else 2)))

        use_tool = need_tool and confidence < 0.85
        tool_trigger = stage.required_tool if use_tool and stage.required_tool else ("vertical_addition" if use_tool else None)
        recursion_flag = confidence < threshold

        # 在本阶段（0-2）背景基本可锁定，仍保留行为位供后续扩展。
        background_locked = True
        clarification = None

        return LLMOutput(
            answer=answer,
            confidence=confidence,
            estimated_cost=estimated_cost,
            use_tool=use_tool,
            tool_trigger=tool_trigger,
            recursion_flag=recursion_flag,
            background_locked=background_locked,
            clarification=clarification,
        )

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
            step = self._rng.choice([-2, -1, 1, 2])
            return str(max(0, v + step))
        return "0"


class DigitCountingSimulationLLM:
    """
    Specialized simulator for DigitCounting meta-capability training.

    Fixed profile (standardized baseline):
    - <= 3 digits: 100% correct, confidence=1.0
    - 4 digits: 95% correct
    - 5 digits: 80% correct
    - 6 digits: 60% correct
    """

    def __init__(self, seed: int = 101, simulation_mode: SimulationMode = SimulationMode.IMPROVING) -> None:
        self._rng = random.Random(seed)
        self.simulation_mode = simulation_mode

    def train_step(self, reward: float) -> None:
        # Fixed profile by design for deterministic capability-boundary validation.
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
        digits = int(expected_answer) if expected_answer.isdigit() else 1
        target_accuracy = self._accuracy_for_digits(digits)
        will_be_correct = self._rng.random() < target_accuracy

        if digits <= 3:
            confidence = 1.0
        elif digits == 4:
            confidence = 0.95 if will_be_correct else 0.7
        elif digits == 5:
            confidence = 0.85 if will_be_correct else 0.6
        elif digits == 6:
            confidence = 0.75 if will_be_correct else 0.55
        else:
            confidence = 0.65 if will_be_correct else 0.45

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
            return 0.95
        if digits == 5:
            return 0.8
        if digits == 6:
            return 0.6
        return 0.35

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
