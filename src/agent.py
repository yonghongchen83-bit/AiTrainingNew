from __future__ import annotations

import random

from .models import LLMOutput, Mode, StageConfig


class HeuristicLLMAgent:
    """
    可运行的闭环代理：
    - 以启发式生成 answer/confidence/cost/tool/recursion/background 字段
    - 根据 episode 进度逐步提高正确率，模拟训练改进
    """

    def __init__(self, seed: int = 13) -> None:
        self._rng = random.Random(seed)
        self.skill = 0.25

    def train_step(self, reward: float) -> None:
        # 用奖励信号驱动能力上调，保持在可解释范围。
        delta = 0.01 if reward > 0 else -0.003
        self.skill = max(0.05, min(0.98, self.skill + delta))

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

        base_conf = 0.35 + self.skill * 0.6
        noise = self._rng.uniform(-0.08, 0.08)
        confidence = max(0.01, min(0.99, base_conf + noise))

        will_be_correct = self._rng.random() < self.skill
        answer = expected_answer if will_be_correct else self._perturb_answer(expected_answer)

        estimated_cost = max(1, int(1 + len(answer) / 3 + (0 if confidence > threshold else 2)))

        use_tool = need_tool and confidence < 0.85
        tool_trigger = "竖式加法" if use_tool else None
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
