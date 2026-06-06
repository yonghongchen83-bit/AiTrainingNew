# AITraining2

Minimal runnable closed loop for the meta-cognitive training architecture defined in Docs/AiDevelopmenPlan.txt.

This runtime includes an official swappable LLM provider layer so framework verification can run with a simulated backend or a real-provider stub.

## Run

```bash
python main.py --episodes 120
```

Run with explicit simulated provider:

```bash
python main.py --episodes 120 --llm-provider simulated --out run_summary_simulated.json
```

Run with real-provider stub wiring (no external API calls):

```bash
python main.py --episodes 40 --llm-provider real_stub --llm-model gpt-5.3-codex --out run_summary_real_stub.json
```

Run with real vLLM provider (OpenAI-compatible local endpoint):

1. Start a tiny Hugging Face model with vLLM (example):

```bash
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-0.5B-Instruct --host 127.0.0.1 --port 8000
```

2. Run DigitCounting boundary discovery against real model:

```bash
python main.py --episodes 120 --llm-provider real_vllm --llm-model Qwen/Qwen2.5-0.5B-Instruct --llm-base-url http://127.0.0.1:8000/v1 --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --out run_summary_vllm_tiny_digit_test.json
```

Run RLHF training workspace orchestrator (dry-run):

```bash
python scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 42 --dry-run
```

Run RLHF training workspace orchestrator (materialized placeholders + Ollama handoff bundle):

```bash
python scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 43
```

After a run completes, use the generated bundle under `training/runs/<run_id>/ollama/`:

```bash
ollama create stage2-confidence -f training/runs/<run_id>/ollama/Modelfile
ollama run stage2-confidence
```

Run full Stage 0-4 loop with self-extension enabled:

```bash
python main.py --episodes 120 --enable-self-extension --self-task-count 60 --out run_summary_phase4.json
```

## Milestone Bootstrap

Use the helper to pre-seed governance docs for a new milestone:

```bash
python scripts/start_milestone.py --name "your milestone" --apply
```

## Scope

- Implements Phase 0-4 runnable loop.
- Uses canonical toolbox tools with multi-trigger alias words.
- Includes official swappable LLM provider abstraction (simulated + real_stub).
- Includes RLHF-only training orchestrator path with run-scoped Ollama handoff bundle output.
