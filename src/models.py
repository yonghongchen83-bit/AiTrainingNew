from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Mode(str, Enum):
    CHAT = "Chat"
    EXPERT = "Expert"
    AUDIT = "Audit"


class FailureType(str, Enum):
    NONE = "None"
    BUDGET_EXHAUSTED = "BudgetExhausted"
    VALIDATION_FAILED = "ValidationFailed"
    IRREDUCIBLE_UNCERTAINTY = "IrreducibleUncertainty"


@dataclass
class LLMOutput:
    answer: str
    confidence: float
    estimated_cost: int
    use_tool: bool
    tool_trigger: Optional[str]
    recursion_flag: bool
    background_locked: bool
    clarification: Optional[str]


@dataclass
class StageConfig:
    index: int
    name: str
    tool_required: bool
    required_tool: Optional[str]
    need_background_locking: bool
    encourage_recursion: bool
    penalize_surprise: bool = True


@dataclass
class StageMetrics:
    episodes: int = 0
    success_count: int = 0
    surprise_sum: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.episodes == 0:
            return 0.0
        return self.success_count / self.episodes

    @property
    def mean_surprise(self) -> float:
        if self.episodes == 0:
            return 1.0
        return self.surprise_sum / self.episodes


@dataclass
class Tool:
    trigger: str
    description: str
    usage_count: int = 0
    cache_level: str = "L2"
    must_keep: bool = False


@dataclass
class EpisodeRecord:
    stage_name: str
    question: str
    answer: str
    expected: str
    success: bool
    confidence: float
    surprise: float
    reward: float
    cost: float
    used_tool: Optional[str]
    recursion_flag: bool
    background_locked: bool
    failure_type: FailureType = FailureType.NONE


@dataclass
class RuntimeStats:
    total_episodes: int = 0
    total_reward: float = 0.0
    false_high_confidence: int = 0
    budget_efficiency_product: float = 1.0
    budget_efficiency_count: int = 0
    stage_metrics: dict[str, StageMetrics] = field(default_factory=dict)


@dataclass
class RewardProfile:
    penalize_surprise_weight: float = 2.0
    success_reward: float = 1.0
    failure_penalty: float = -0.5
    cost_overrun_penalty: float = -0.3
    low_cost_bonus: float = 0.2
    recursion_bonus: float = 0.5
    background_lock_bonus: float = 0.8
    clarification_bonus: float = 0.2


@dataclass
class GeneratedTask:
    stage_name: str
    question: str
    expected_answer: str
    difficulty: int
