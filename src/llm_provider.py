from __future__ import annotations

from abc import ABC, abstractmethod

from .agent import DigitCountingSimulationLLM, HeuristicLLMAgent
from .models import LLMOutput, LLMProviderType, Mode, SimulationMode, StageConfig


class LLMProvider(ABC):
    @property
    @abstractmethod
    def provider_type(self) -> str:
        raise NotImplementedError()

    @property
    def model_name(self) -> str | None:
        return None

    def learning_progress(self) -> float:
        # Unknown providers default to neutral progress.
        return 0.5

    @abstractmethod
    def train_step(self, reward: float) -> None:
        raise NotImplementedError()

    @abstractmethod
    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        raise NotImplementedError()


class SimulatedLLMProvider(LLMProvider):
    def __init__(self, seed: int, simulation_mode: SimulationMode) -> None:
        self._agent = HeuristicLLMAgent(seed=seed, simulation_mode=simulation_mode)
        self._digit_counting_agent = DigitCountingSimulationLLM(seed=seed + 17, simulation_mode=simulation_mode)

    @property
    def provider_type(self) -> str:
        return LLMProviderType.SIMULATED.value

    def learning_progress(self) -> float:
        return self._agent.skill

    def train_step(self, reward: float) -> None:
        self._agent.train_step(reward)
        self._digit_counting_agent.train_step(reward)

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        if stage.name == "DigitCounting":
            return self._digit_counting_agent.predict(
                question=question,
                expected_answer=expected_answer,
                budget=budget,
                mode=mode,
                stage=stage,
            )

        return self._agent.predict(
            question=question,
            expected_answer=expected_answer,
            budget=budget,
            mode=mode,
            stage=stage,
        )


class RealLLMProviderStub(LLMProvider):
    def __init__(self, model_name: str = "gpt-5.3-codex") -> None:
        self._model_name = model_name

    @property
    def provider_type(self) -> str:
        return LLMProviderType.REAL_STUB.value

    @property
    def model_name(self) -> str | None:
        return self._model_name

    def train_step(self, reward: float) -> None:
        # Real providers are usually stateless at runtime; training signals are logged externally.
        _ = reward

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        _ = (question, expected_answer, budget, mode)
        tool_trigger = stage.required_tool if stage.tool_required else None
        return LLMOutput(
            answer="0",
            confidence=0.2,
            estimated_cost=3,
            use_tool=stage.tool_required,
            tool_trigger=tool_trigger,
            recursion_flag=True,
            background_locked=True,
            clarification="real_llm_provider_stub_active",
        )


def build_llm_provider(
    provider_type: LLMProviderType,
    seed: int,
    simulation_mode: SimulationMode,
    model_name: str | None = None,
) -> LLMProvider:
    if provider_type == LLMProviderType.REAL_STUB:
        return RealLLMProviderStub(model_name=model_name or "gpt-5.3-codex")
    return SimulatedLLMProvider(seed=seed, simulation_mode=simulation_mode)
