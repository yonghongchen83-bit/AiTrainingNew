from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import re
from urllib import error, request

from .agent import HeuristicLLMAgent
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

    @property
    def provider_type(self) -> str:
        return LLMProviderType.SIMULATED.value

    def learning_progress(self) -> float:
        return self._agent.skill

    def train_step(self, reward: float) -> None:
        self._agent.train_step(reward)

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
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


class RealVLLMProvider(LLMProvider):
    def __init__(self, model_name: str, base_url: str | None = None) -> None:
        self._model_name = model_name
        self._base_url = (base_url or os.getenv("VLLM_BASE_URL") or "http://127.0.0.1:8000/v1").rstrip("/")
        self._api_key = os.getenv("VLLM_API_KEY")
        self._timeout_sec = float(os.getenv("VLLM_TIMEOUT_SEC", "4"))

    @property
    def provider_type(self) -> str:
        return LLMProviderType.REAL_VLLM.value

    @property
    def model_name(self) -> str | None:
        return self._model_name

    def train_step(self, reward: float) -> None:
        _ = reward

    @staticmethod
    def _threshold(mode: Mode) -> float:
        if mode == Mode.CHAT:
            return 0.4
        if mode == Mode.EXPERT:
            return 0.8
        return 0.9

    @staticmethod
    def _extract_answer_fallback(text: str) -> str:
        match = re.search(r"-?\d+", text)
        if match:
            return match.group(0)
        return "0"

    @staticmethod
    def _extract_json_block(text: str) -> dict | None:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict):
            return payload
        return None

    def _query_vllm(self, question: str) -> tuple[str, int, str | None]:
        system_prompt = (
            "You are a careful math assistant. "
            "Return JSON only with keys: answer (string), confidence (number 0 to 1)."
        )
        user_prompt = f"Question: {question}"
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 64,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self._base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self._api_key:
            req.add_header("Authorization", f"Bearer {self._api_key}")

        with request.urlopen(req, timeout=self._timeout_sec) as resp:
            raw = resp.read().decode("utf-8")

        payload = json.loads(raw)
        content = str(payload["choices"][0]["message"]["content"])
        usage = payload.get("usage", {})
        estimated_tokens = int(usage.get("total_tokens", max(8, len(content) // 4)))
        return content, estimated_tokens, None

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        _ = (expected_answer, budget)
        try:
            content, estimated_tokens, clarification = self._query_vllm(question)
            parsed = self._extract_json_block(content)
            if parsed is None:
                answer = self._extract_answer_fallback(content)
                confidence = 0.35
            else:
                answer = str(parsed.get("answer", self._extract_answer_fallback(content))).strip()
                try:
                    confidence = float(parsed.get("confidence", 0.35))
                except (TypeError, ValueError):
                    confidence = 0.35
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError) as ex:
            answer = "0"
            confidence = 0.15
            estimated_tokens = 16
            clarification = f"real_vllm_provider_error:{type(ex).__name__}"

        confidence = max(0.01, min(1.0, confidence))
        recursion_flag = confidence < self._threshold(mode)

        return LLMOutput(
            answer=answer,
            confidence=confidence,
            estimated_cost=max(1, estimated_tokens // 8),
            use_tool=False,
            tool_trigger=None,
            recursion_flag=recursion_flag,
            background_locked=True,
            clarification=clarification,
        )


class RealLocalProvider(LLMProvider):
    """Loads a HuggingFace model directly in-process — no external server needed."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None
        self._tokenizer = None

    @property
    def provider_type(self) -> str:
        return LLMProviderType.REAL_LOCAL.value

    @property
    def model_name(self) -> str | None:
        return self._model_name

    def train_step(self, reward: float) -> None:
        _ = reward

    @staticmethod
    def _threshold(mode: Mode) -> float:
        if mode == Mode.CHAT:
            return 0.4
        if mode == Mode.EXPERT:
            return 0.8
        return 0.9

    @staticmethod
    def _extract_answer_fallback(text: str) -> str:
        match = re.search(r"-?\d+", text)
        if match:
            return match.group(0)
        return "0"

    @staticmethod
    def _extract_json_block(text: str) -> dict | None:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict):
            return payload
        return None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        print(f"[RealLocalProvider] Loading {self._model_name} ...")
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_name,
            device_map="auto",
            torch_dtype="auto",
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        print(f"[RealLocalProvider] {self._model_name} loaded.")

    def predict(
        self,
        question: str,
        expected_answer: str,
        budget: float,
        mode: Mode,
        stage: StageConfig,
    ) -> LLMOutput:
        _ = (expected_answer, budget)
        try:
            self._ensure_loaded()
            system_prompt = (
                "You are a careful math assistant. "
                "Return JSON only with keys: answer (string), confidence (number 0 to 1)."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}"},
            ]
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=64,
                temperature=0.0,
                do_sample=False,
                pad_token_id=self._tokenizer.pad_token_id,
            )
            generated = outputs[0][inputs["input_ids"].shape[1]:]
            content = self._tokenizer.decode(generated, skip_special_tokens=True).strip()
            estimated_tokens = len(generated)

            parsed = self._extract_json_block(content)
            if parsed is None:
                answer = self._extract_answer_fallback(content)
                confidence = 0.35
            else:
                answer = str(parsed.get("answer", self._extract_answer_fallback(content))).strip()
                try:
                    confidence = float(parsed.get("confidence", 0.35))
                except (TypeError, ValueError):
                    confidence = 0.35
            clarification = None
        except Exception as ex:
            answer = "0"
            confidence = 0.15
            estimated_tokens = 16
            clarification = f"real_local_error:{type(ex).__name__}"

        confidence = max(0.01, min(1.0, confidence))
        recursion_flag = confidence < self._threshold(mode)

        return LLMOutput(
            answer=answer,
            confidence=confidence,
            estimated_cost=max(1, estimated_tokens // 8),
            use_tool=False,
            tool_trigger=None,
            recursion_flag=recursion_flag,
            background_locked=True,
            clarification=clarification,
        )


def build_llm_provider(
    provider_type: LLMProviderType,
    seed: int,
    simulation_mode: SimulationMode,
    model_name: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    if provider_type == LLMProviderType.REAL_STUB:
        return RealLLMProviderStub(model_name=model_name or "gpt-5.3-codex")
    if provider_type == LLMProviderType.REAL_VLLM:
        return RealVLLMProvider(model_name=model_name or "Qwen/Qwen2.5-0.5B-Instruct", base_url=base_url)
    if provider_type == LLMProviderType.REAL_LOCAL:
        return RealLocalProvider(model_name=model_name or "Qwen/Qwen2.5-0.5B-Instruct")
    return SimulatedLLMProvider(seed=seed, simulation_mode=simulation_mode)
