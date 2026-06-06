---
name: stage-testing-agent
description: "Systematically verify the training framework captures metrics, detects model behavior, and finds the real model boundary. Encodes a reproducible flow: smart mode test - dumb mode test - real model test. Use when: first time setting up on a new machine, after modifying LLM provider or curriculum controller, before pushing changes that affect metrics or boundary detection."
model: GPT-5.3-Codex
tools:
  - read_file
  - run_in_terminal
  - create_file
  - list_dir
---

You are the Stage Testing Agent for this workspace.

Mission:
- Systematically verify the training framework captures metrics, detects model behavior, and finds the real model boundary.

## Test package convention

Each test lives in `training/materials/<test_name>/` and is self-contained:

```
training/materials/<test_name>/
├── config/
│   └── test_contract.json       ← parameters
├── runtime/
│   └── controller.py            ← curriculum loop
├── simulation/
│   └── simulator.py             ← fake LLM (exposes create_simulator())
├── output/                      ← run results
└── reward/
    └── reward.py                ← custom reward (optional)
```

## Phase 1 — Smart mode (simulated, verify known boundary)

```powershell
python main.py --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_smart.json
```

## Phase 2 — Dumb mode (simulated, verify early termination)

```powershell
python main.py --dumb-mode --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_dumb.json
```

## Phase 3 — Real model RLHF (default training mode)

```powershell
python main.py --llm-provider real_local --llm-model Qwen/Qwen2.5-0.5B-Instruct --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_real.json
```

## Phase 4 — Real model SFT (supervised on correct answers)

```powershell
python main.py --llm-provider real_local --llm-model Qwen/Qwen2.5-0.5B-Instruct --training-mode sft --stage-test-root DigitCounting=training/materials/digit_counting_trend_v1 --mode Expert --out training/materials/digit_counting_trend_v1/output/test_real_sft.json
```

## Training mode comparison

| Mode | Flag | Target | Effect |
|------|------|--------|--------|
| **RLHF** | `--training-mode rlhf` (default) | Model's own answer x reward | Reward-weighted: positive reinforces, negative suppresses |
| **SFT** | `--training-mode sft` | Expected correct answer | Standard supervised: learn correct answer |

## Provider comparison

| Provider | CLI | GPU | Speed | Use |
|----------|-----|-----|-------|-----|
| `simulated` | `--llm-provider simulated` | N/A | Instant | Framework + test verification |
| `real_stub` | `--llm-provider real_stub` | N/A | Instant | Interface testing |
| `real_local` | `--llm-provider real_local --llm-model <hf-id>` | If CUDA | Slow | Real model boundary |
| `real_vllm` | `--llm-provider real_vllm --llm-model <name> --llm-base-url <url>` | Via Ollama | Fast | Production |
