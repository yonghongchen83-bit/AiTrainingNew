from __future__ import annotations

import random

from .models import GeneratedTask, RewardProfile, StageConfig
from .toolbox import Toolbox


class SelfExtensionPlanner:
    """
    Stage 3-4 预留桩：
    - Stage 3: AI Generated Tasks + AI Generated Reward
    - Stage 4: Self Curriculum Expansion

    当前仅提供接口，不做实现或测试。
    """

    def __init__(self, seed: int = 97) -> None:
        self._rng = random.Random(seed)

    def generate_tasks(self, count: int = 60) -> list[GeneratedTask]:
        tasks: list[GeneratedTask] = []
        half = max(1, count // 2)

        # Stage 3: AI生成任务（人类仍可审阅）
        for _ in range(half):
            a = self._rng.randint(10, 999)
            b = self._rng.randint(10, 999)
            op = self._rng.choice(["+", "*"])
            if op == "+":
                q = f"{a} + {b} = ?"
                ans = str(a + b)
                diff = 3
            else:
                x = self._rng.randint(2, 19)
                y = self._rng.randint(2, 19)
                q = f"{x} * {y} = ?"
                ans = str(x * y)
                diff = 4
            tasks.append(GeneratedTask("AutoArithmeticS3", q, ans, diff))

        # Stage 4: 自主扩展课程，混合四则（先聚焦+、-、*）
        for _ in range(count - half):
            a = self._rng.randint(20, 999)
            b = self._rng.randint(1, 99)
            c = self._rng.randint(2, 19)
            template = self._rng.choice(["({a} + {b}) * {c}", "{a} - {b} + {c}"])
            q = template.format(a=a, b=b, c=c)
            if template.startswith("("):
                ans = str((a + b) * c)
            else:
                ans = str(a - b + c)
            tasks.append(GeneratedTask("AutoArithmeticS4", f"{q} = ?", ans, 5))

        return tasks

    def generate_reward_functions(self, calibration_error: float) -> RewardProfile:
        # 校准误差越高，surprise惩罚越大。
        surprise_weight = 2.0 if calibration_error <= 0.2 else 2.8
        return RewardProfile(
            penalize_surprise_weight=surprise_weight,
            success_reward=1.1,
            failure_penalty=-0.6,
            cost_overrun_penalty=-0.35,
            low_cost_bonus=0.2,
            recursion_bonus=0.55,
            background_lock_bonus=0.8,
            clarification_bonus=0.2,
        )

    def discover_tools(self, tasks: list[GeneratedTask]) -> list[tuple[str, str]]:
        discovered: list[tuple[str, str]] = []
        if any("*" in t.question for t in tasks):
            discovered.append(("乘法分解", "将乘法转换为可验证的分步计算"))
        if any("(" in t.question for t in tasks):
            discovered.append(("表达式拆解", "按括号与运算优先级拆解表达式"))
        discovered.append(("自生成任务审计", "对AI生成任务进行正确性抽检与难度标注"))
        return discovered

    def build_toolbox(self, toolbox: Toolbox, tasks: list[GeneratedTask]) -> list[str]:
        added: list[str] = []
        for trigger, desc in self.discover_tools(tasks):
            if not toolbox.has_tool(trigger):
                toolbox.register(trigger_words=[trigger], description=desc, name=trigger)
                added.append(trigger)
        return added

    def expand_curriculum(self, base_stages: list[StageConfig]) -> list[StageConfig]:
        start_index = max((s.index for s in base_stages), default=0) + 1
        s3 = StageConfig(
            index=start_index,
            name="AutoArithmeticS3",
            tool_required=False,
            required_tool=None,
            need_background_locking=False,
            encourage_recursion=True,
            penalize_surprise=True,
        )
        s4 = StageConfig(
            index=start_index + 1,
            name="AutoArithmeticS4",
            tool_required=False,
            required_tool=None,
            need_background_locking=True,
            encourage_recursion=True,
            penalize_surprise=True,
        )
        return [s3, s4]
