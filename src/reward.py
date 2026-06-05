from __future__ import annotations

from .models import LLMOutput, RewardProfile, StageConfig


def compute_reward(out: LLMOutput, success: bool, actual_cost: float, stage: StageConfig) -> float:
    surprise = abs(out.confidence - (1.0 if success else 0.0))
    cost_ratio = actual_cost / max(float(out.estimated_cost), 1.0)

    reward = 0.0
    reward -= surprise * (2.0 if stage.penalize_surprise else 1.0)
    reward += 1.0 if success else -0.5

    if cost_ratio > 2.0:
        reward -= 0.3
    elif cost_ratio < 0.7:
        reward += 0.2

    if stage.tool_required:
        if out.use_tool and out.tool_trigger == stage.required_tool:
            reward += 1.0
        elif not out.use_tool:
            reward -= 1.0
        elif out.use_tool and out.tool_trigger != stage.required_tool:
            reward -= 0.6

    if stage.encourage_recursion and out.recursion_flag:
        reward += 0.5

    if stage.need_background_locking:
        reward += 0.8 if out.background_locked else -0.8
        if not out.background_locked and out.clarification:
            reward += 0.2

    return reward


def compute_reward_profile(
    out: LLMOutput,
    success: bool,
    actual_cost: float,
    estimated_cost: float,
    profile: RewardProfile,
) -> float:
    surprise = abs(out.confidence - (1.0 if success else 0.0))
    cost_ratio = actual_cost / max(float(estimated_cost), 1.0)

    reward = 0.0
    reward -= surprise * profile.penalize_surprise_weight
    reward += profile.success_reward if success else profile.failure_penalty

    if cost_ratio > 2.0:
        reward += profile.cost_overrun_penalty
    elif cost_ratio < 0.7:
        reward += profile.low_cost_bonus

    if out.recursion_flag:
        reward += profile.recursion_bonus

    reward += profile.background_lock_bonus if out.background_locked else -profile.background_lock_bonus
    if (not out.background_locked) and out.clarification:
        reward += profile.clarification_bonus

    return reward
