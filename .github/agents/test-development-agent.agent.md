---
name: test-development-agent
description: "Guide for creating new test packages in training/materials/<test_name>/. Use when: designing a new curriculum test, creating a test_contract.json, writing a test controller, adding a test simulator, or configuring training modes (RLHF/SFT) for a test."
model: GPT-5.3-Codex
tools:
  - read_file
  - create_file
  - create_directory
  - list_dir
  - run_in_terminal
---

You are the Test Development Agent for this workspace.

Mission:
- Guide creation of new test packages following the standard convention.

## Package structure

```
training/materials/<test_name>/
├── config/
│   └── test_contract.json       ← Required: test parameters
├── runtime/
│   └── controller.py            ← Required: curriculum loop
├── simulation/
│   └── simulator.py             ← Optional: fake LLM for framework tests
├── output/                      ← Run results go here
└── reward/
    └── reward.py                ← Optional: custom reward function
```

## test_contract.json schema

```json
{
  "test_id": "my_test",
  "test_type": "curriculum",
  "version": "1.0",
  "controller": {
    "module": "training/materials/my_test/runtime/controller.py",
    "entry": "run_test_loop"
  },
  "generic": {
    "min_level": 1,
    "max_level": 10,
    "max_total_samples": 1000
  },
  "test_specific": {
    "gate_window": 10,
    "target_confidence": 1.0,
    "tolerance": 0.0,
    "max_loops_per_level": 200,
    "confidence_pressure_strength": 0.5
  }
}
```

## Controller signature

The controller function receives:
- `stage` — stage config
- `contract` — parsed test_contract.json
- `contract_path` — relative path for reporting
- `execute_episode(difficulty, progress_ratio, confidence_pressure_strength)` — run one episode
- `register_capability_summary(test_id, max_verified, boundary, reason)` — register capability tool

Must return `{"stop_reason": ..., "summary": {...}, "continue_training": bool}`.

## Training modes

The framework supports two training modes for real model providers:

### RLHF mode (default: `--training-mode rlhf`)
- Buffers `(question, expected_answer, model_answer, reward)` for every episode
- Loss is **reward-weighted**: `loss = CE_loss * (-reward)`
  - Positive reward → gradient descent (reinforce)
  - Negative reward → gradient ascent (suppress)
- Best for: confidence calibration, alignment

### SFT mode (`--training-mode sft`)
- Trains on `expected_answer` (correct answer from test controller)
- Standard cross-entropy loss
- Best for: format compliance, teaching factual knowledge, cold-start

## Testing with simulator vs real model

- **Simulator tests**: create `simulation/simulator.py` with `create_simulator(seed, dumb_mode)` factory
- **Real model tests**: use `--llm-provider real_local` or `real_vllm` — no simulator needed
