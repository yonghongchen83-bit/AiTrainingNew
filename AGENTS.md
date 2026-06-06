# Workspace Agents

## milestone-governor

```yaml
name: milestone-governor
instructions: |
  Enforce implementation visibility and milestone-based git commits.

  When to use:
  - Any coding or architecture task in this repository.
  - Any request that changes modules or execution flow.

  Governance requirements:
  - Keep checkbox progress updated in Docs/ImplementationProgress.md.
  - Keep formal plan updated in Docs/ImplementationPlan.md.
  - Log architecture decisions in Docs/ArchitectureDecisionLog.md.
  - Log module interaction changes in Docs/ModuleInteractionSpec.md.
  - Log execution commands and key outputs in Docs/ExecutionLog.md.
  - Commit once per completed milestone with message prefix: milestone: <name>.
```

## stage-testing-agent

```yaml
name: stage-testing-agent
instructions: |
  Systematically verify the training framework captures metrics, detects model
  behavior, and finds the real model boundary.

  Encodes a reproducible flow: smart mode test → dumb mode test → real model test.

  When to use:
  - First time setting up this project on a new machine.
  - After modifying the LLM provider layer or curriculum controller.
  - Before pushing changes that affect metrics capture or boundary detection.

  ## Test package convention

  Each test lives in `training/materials/<test_name>/` and is self-contained:

  ```
  training/materials/<test_name>/
  ├── config/test_contract.json       ← parameters
  ├── runtime/controller.py            ← curriculum loop
  ├── simulation/simulator.py          ← fake LLM (exposes create_simulator())
  ├── output/                          ← run results
  └── reward/reward.py                 ← custom reward (optional)
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

  ### Training mode comparison

  | Mode | Flag | Target | Effect |
  |------|------|--------|--------|
  | **RLHF** | `--training-mode rlhf` (default) | Model's own answer × reward | Reward-weighted: positive reinforces, negative suppresses |
  | **SFT** | `--training-mode sft` | Expected correct answer | Standard supervised: learn correct answer |

  ## Provider comparison

  | Provider | CLI | GPU | Speed | Use |
  |----------|-----|-----|-------|-----|
  | `simulated` | `--llm-provider simulated` | N/A | Instant | Framework + test verification |
  | `real_stub` | `--llm-provider real_stub` | N/A | Instant | Interface testing |
  | `real_local` | `--llm-provider real_local --llm-model <hf-id>` | If CUDA | Slow | Real model boundary |
  | `real_vllm` | `--llm-provider real_vllm --llm-model <name> --llm-base-url <url>` | Via Ollama | Fast | Production |

  ## Troubleshooting

  | Symptom | Cause | Fix |
  |---------|-------|-----|
  | Always `confidence=0.35` | Model can't output JSON | Check raw model output; may need prompt tweaking |
  | `real_vllm` timeouts | Ollama not running | `curl http://localhost:11434/api/tags` to verify |
```

## test-development-agent

```yaml
name: test-development-agent
instructions: |
  Guide for creating new test packages in `training/materials/<test_name>/`.

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
```
