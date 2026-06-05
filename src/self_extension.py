from __future__ import annotations


class SelfExtensionPlanner:
    """
    Stage 3-4 预留桩：
    - Stage 3: AI Generated Tasks + AI Generated Reward
    - Stage 4: Self Curriculum Expansion

    当前仅提供接口，不做实现或测试。
    """

    def generate_tasks(self) -> None:
        raise NotImplementedError("Stage 3-4 stub: generate_tasks is not implemented")

    def generate_reward_functions(self) -> None:
        raise NotImplementedError("Stage 3-4 stub: generate_reward_functions is not implemented")

    def expand_curriculum(self) -> None:
        raise NotImplementedError("Stage 3-4 stub: expand_curriculum is not implemented")
