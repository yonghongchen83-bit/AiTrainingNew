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

    def predict_confidence(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
        force_confidence: bool = False,
    ) -> LLMOutput:
        if force_confidence:
            return LLMOutput(answer="", confidence=1.0, estimated_cost=1, use_tool=False, tool_trigger=None, recursion_flag=False, background_locked=True, clarification="force_solve")
        threshold = self._threshold(mode)
        need_tool = stage.tool_required

        if self.simulation_mode == SimulationMode.IMPROVING:
            base_conf = 0.35 + self.skill * 0.6
            noise = self._rng.uniform(-0.08, 0.08)
        else:
            base_conf = 0.18 + self.skill * 0.4
            noise = self._rng.uniform(-0.22, 0.22)

        confidence = max(0.01, min(1.0, base_conf + noise))
        if self.simulation_mode == SimulationMode.IMPROVING and self.skill >= 0.985:
            confidence = 1.0

        estimated_cost = max(1, int(1 + len(expected_answer) / 3 + (0 if confidence > threshold else 2)))

        use_tool = need_tool and confidence < 0.85
        tool_trigger = stage.required_tool if use_tool and stage.required_tool else ("vertical_addition" if use_tool else None)
        recursion_flag = confidence < threshold

        background_locked = True
        clarification = None

        return LLMOutput(
            answer="",
            confidence=confidence,
            estimated_cost=estimated_cost,
            use_tool=use_tool,
            tool_trigger=tool_trigger,
            recursion_flag=recursion_flag,
            background_locked=background_locked,
            clarification=clarification,
        )

    def generate_answer(
        self,
        question: str,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        """Actually answer the question. Uses the internal skill model."""
        _ = (question, mode, stage)
        if self.simulation_mode == SimulationMode.IMPROVING:
            will_be_correct = self._rng.random() < self.skill
            base_conf = 0.35 + self.skill * 0.6
            noise = self._rng.uniform(-0.08, 0.08)
        else:
            will_be_correct = self._rng.random() < 0.12
            base_conf = 0.18 + self.skill * 0.4
            noise = self._rng.uniform(-0.22, 0.22)

        confidence = max(0.01, min(1.0, base_conf + noise))
        if self.simulation_mode == SimulationMode.IMPROVING and self.skill >= 0.985 and will_be_correct:
            confidence = 1.0

        return LLMOutput(
            answer=self._engineered_answer(expected_answer, will_be_correct),
            confidence=confidence,
            estimated_cost=max(1, 1 + len(expected_answer) // 3),
            use_tool=False,
            tool_trigger=None,
            recursion_flag=False,
            background_locked=True,
            clarification=None,
        )

    def _engineered_answer(self, expected_answer: str, will_be_correct: bool) -> str:
        if will_be_correct:
            return expected_answer
        if expected_answer.isdigit():
            v = int(expected_answer)
            step = self._rng.choice([-2, -1, 1, 2])
            return str(max(0, v + step))
        return "0"

    @staticmethod
    def _threshold(mode: Mode) -> float:
        if mode == Mode.CHAT:
            return 0.4
        if mode == Mode.EXPERT:
            return 0.8
        return 0.9
