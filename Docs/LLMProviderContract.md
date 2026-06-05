# LLM Provider Contract (Official)

Last Updated: 2026-06-06

## Purpose

This project now treats LLM execution as a swappable provider layer so the training framework can be verified independently from a real model runtime.

## Contract Surface

The provider contract lives in src/llm_provider.py and requires these behaviors:

- provider_type: stable provider identifier
- model_name: optional model metadata
- predict(question, expected_answer, budget, mode, stage) -> LLMOutput
- train_step(reward) -> None
- learning_progress() -> float

Trainer code uses only this contract and is not coupled to a specific provider implementation.

## Built-in Providers

1. simulated
- Class: SimulatedLLMProvider
- Backend behavior: wraps heuristic simulated agent
- Use case: deterministic framework verification and regression testing

2. real_stub
- Class: RealLLMProviderStub
- Backend behavior: runtime-safe placeholder for future real LLM integration
- Use case: test provider wiring and framework orchestration before external API integration

## Runtime Selection

CLI options in main.py:

- --llm-provider simulated|real_stub
- --llm-model <name>

Examples:

- python main.py --episodes 120 --llm-provider simulated --out run_summary.json
- python main.py --episodes 40 --llm-provider real_stub --llm-model gpt-5.3-codex --out run_summary_real_stub.json

## Output Evidence

Run summaries now include:

- llm_provider.type
- llm_provider.model

This allows downstream analysis to distinguish framework behavior by provider backend.

## Integration Path for Real LLM

When adding real API execution in later stages:

1. Implement a new provider class in src/llm_provider.py or adjacent module.
2. Keep the same provider contract methods.
3. Add provider type to LLMProviderType enum.
4. Extend build_llm_provider factory.
5. Keep simulated provider unchanged for framework-only verification and regression baselines.
