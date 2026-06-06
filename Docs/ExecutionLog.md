# Execution Log

Last Updated: 2026-06-06

## Run 001

- Command: python main.py --episodes 120 --out run_summary.json
- Status: Success
- Output Artifact: run_summary.json

### Key Metrics

- episodes: 120
- total_reward: -134.2747
- calibration_error: 0.4407
- false_high_confidence: 0
- budget_efficiency: 1.0

### Stage Metrics

- PlaceValue: success_rate=0.35, mean_surprise=0.499, episodes=40
- DigitCounting: success_rate=0.125, mean_surprise=0.4265, episodes=40
- Addition1Digit: success_rate=0.05, mean_surprise=0.3966, episodes=40

### Notes

- This is a runnable closed loop baseline, not tuned performance.
- Current agent is heuristic and reward-driven; results establish execution validity.

## Run 002

- Command: git init
- Status: Success
- Result: Local repository initialized at workspace root.

## Run 003

- Command: git add .; git commit -m "milestone: runnable stage 0-2 closed loop with docs"
- Status: Success
- Commit: f935df4

## Run 004

- Action: Create workspace governance agent and registration docs
- Files:
	- .github/agents/milestone-governor.agent.md
	- AGENTS.md
	- .gitignore

## Run 005

- Command: git rm -r --cached src/__pycache__; git add .; git commit -m "milestone: workspace governance agent and git policy"
- Status: Success
- Commit: 47dae8b

## Run 006

- Action: Add deterministic workspace hooks and validator script
- Files:
	- .github/hooks/milestone-governance.json
	- scripts/validate_milestone_commit.py

## Run 007

- Command: "{}" | python scripts/validate_milestone_commit.py --event SessionStart; "{}" | python scripts/validate_milestone_commit.py --event PostToolUse
- Status: Success
- Result: Hook script returned valid JSON responses for both events.

## Run 008

- Action: Extend governance hooks with PreToolUse event and strict milestone commit message prefix validation.
- Files:
	- .github/hooks/milestone-governance.json
	- scripts/validate_milestone_commit.py

## Run 009

- Command: PreToolUse validator smoke test with milestone-prefixed and non-prefixed commit messages
- Status: Success
- Result: milestone-prefixed message allowed; non-prefixed message denied.

## Run 010

- Command: git add governance hook updates and docs; git commit -m "milestone: strict commit message enforcement"
- Status: Success

## Run 011

- Command: python scripts/start_milestone.py --name "minimum governance loop" --apply
- Status: Success
- Result: Milestone template entries seeded into plan/progress/execution docs.

## Milestone Template: minimum governance loop

- Generated: 2026-06-06 04:38
- Planned command: git commit -m "milestone: minimum governance loop"
- Checklist seed:
  - Update Docs/ImplementationPlan.md
  - Update Docs/ImplementationProgress.md
  - Update Docs/ArchitectureDecisionLog.md if architecture changes
  - Update Docs/ModuleInteractionSpec.md if module flow changes
  - Append run evidence in Docs/ExecutionLog.md

## Run 012

- Command: git add milestone bootstrap tool and governance docs; git commit -m "milestone: minimum governance loop automation"
- Status: Success

## Run 013

- Command: python main.py --episodes 120 --enable-self-extension --self-task-count 60 --out run_summary_phase4.json
- Status: Success
- Output Artifact: run_summary_phase4.json
- Result: Stage 3/4 completed with self-generated tasks, dynamic reward profile, and expanded curriculum stages AutoArithmeticS3/AutoArithmeticS4.

## Run 014

- Command: git add Stage 3/4 implementation and docs; git commit -m "milestone: complete all goals stage 3 and stage 4"
- Status: Success

## Run 015

- Command: python main.py --episodes 120 --simulation-mode improving --out run_summary_improving.json
- Status: Success
- Output Artifact: run_summary_improving.json

### Key Metrics

- episodes: 120
- total_reward: -120.0
- simulation_mode: improving
- fallback_events: 120
- tool_invocations: 360

### Notes

- All episodes entered low-confidence unresolved fallback in Expert mode.
- Protocol output now contains OpenAI function tool-call objects for fallback escalation.

## Run 016

- Command: python main.py --episodes 120 --simulation-mode stuck --out run_summary_stuck.json
- Status: Success
- Output Artifact: run_summary_stuck.json

### Key Metrics

- episodes: 120
- total_reward: -120.0
- simulation_mode: stuck
- fallback_events: 120
- tool_invocations: 360

### Notes

- Stuck mode keeps confidence lower than improving mode and sustains fallback-heavy behavior.

## Run 017

- Command: python main.py --episodes 40 --mode Chat --simulation-mode improving --stage-initial-budget 1.2 --out run_summary_budget_depleted.json
- Status: Success
- Output Artifact: run_summary_budget_depleted.json

### Key Metrics

- episodes: 39
- total_reward: -43.9599
- simulation_mode: improving
- fallback_events: 9
- tool_invocations: 9
- dominant reason_code: BudgetExhausted

### Notes

- This run validates explicit budget depletion fallback with `CompletionFailed` reason_code `BudgetExhausted`.

## Run 018

- Command: git add runtime/docs/artifacts; git commit -m "milestone: openai protocol fallback and alias trigger semantics"
- Status: Success
- Commit: fd60c84

## Run 019

- Command: python main.py --episodes 120 --simulation-mode improving --out run_summary_improving.json
- Status: Success
- Output Artifact: run_summary_improving.json

## Run 020

- Command: python main.py --episodes 120 --simulation-mode stuck --out run_summary_stuck.json
- Status: Success
- Output Artifact: run_summary_stuck.json

### Regression Check Result

- improving: fallback_events=9, tool_invocations=27, total_reward=-124.163, calibration_error=0.4545
- stuck: fallback_events=120, tool_invocations=360, total_reward=-120.0, calibration_error=0.3026
- conclusion: improving and stuck behavior is now clearly separated as intended.

## Run 021

- Command: python main.py --episodes 30 --llm-provider simulated --out run_summary_simulated_provider.json
- Status: Success
- Output Artifact: run_summary_simulated_provider.json

### Key Metrics

- episodes: 30
- llm_provider.type: simulated
- llm_provider.model: null
- fallback_events: 0
- tool_invocations: 0

## Run 022

- Command: python main.py --episodes 30 --llm-provider real_stub --llm-model gpt-5.3-codex --out run_summary_real_stub.json
- Status: Success
- Output Artifact: run_summary_real_stub.json

### Key Metrics

- episodes: 30
- llm_provider.type: real_stub
- llm_provider.model: gpt-5.3-codex
- fallback_events: 30
- tool_invocations: 90

### Notes

- This run validates framework execution with non-simulated provider wiring while preserving deterministic, API-free behavior.

## Run 023

- Action: Create official `training/` workspace scaffold for materials/models/runs/registry.
- Status: Success
- Result: Added RLHF (`rlhf_confidence_v1`) and SFT (`sft_framework_patterns_v1`) template folders with data/reward/config structure.

## Run 024

- Command: python scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 42 --dry-run
- Status: Success
- Output Artifact: training/runs/20260605T195151Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- training_mode: rlhf
- checkpoint_retention: [best, last]
- human_approval_required: true

## Run 025

- Command: python scripts/run_training_pipeline.py --config training/materials/sft_framework_patterns_v1/config/training_config.json --seed 43
- Status: Success
- Output Artifact: training/runs/20260605T195152Z_sft_framework_patterns_v1/run_summary.json

### Key Metrics

- training_mode: sft
- checkpoint_retention: [best, last]

## Run 026

- Command: C:/Users/cheny/AppData/Local/Python/pythoncore-3.14-64/python.exe main.py --episodes 120 --simulation-mode improving --out run_summary_digit_curriculum.json
- Status: Success
- Output Artifact: run_summary_digit_curriculum.json

### Key Metrics

- episodes: 240
- stop_reason: DigitCountingCapabilityBoundary@1Digits
- digit_counting.status: stopped_capability_boundary
- digit_counting.max_verified_digits: 0
- digit_counting.boundary_digits: 1
- digit_counting.samples: 200

### Notes

- Runtime now uses unified train+eval curriculum for DigitCounting with strict tolerance=0 gate.
- Per-task fallback remains local to each sample; trainer-level stop is now capability-boundary/requirement based.
- human_approval_required: true

### Notes

- Both modes run through the same orchestrator contract, validating config-driven RLHF/SFT switching.

## Run 026

- Command: python training/scripts/start_training.py --stage stage2 --seed 55 --dry-run
- Status: Success
- Output Artifact: training/runs/20260605T195559Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- training_mode: rlhf
- seed: 55
- status: dry_run

## Run 027

- Command: python training/scripts/promote_stage_model.py --run-id 20260605T195222Z_rlhf_confidence_v1 --stage stage2 --approve --reason "passed human review"
- Status: Success
- Output Artifact: training/models/promoted/stage2.end.model

### Key Metrics

- record_type: promotion_decision
- approved: true
- stage: stage2

## Run 028

- Command: python training/scripts/promote_stage_model.py --run-id 20260605T195222Z_rlhf_confidence_v1 --stage stage2 --reason "audit only no approve"
- Status: Success

### Key Metrics

- record_type: promotion_decision
- approved: false
- stage: stage2

## Run 029

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 120 --simulation-mode improving --out run_summary_digit_specialized_validation.json
- Status: Success
- Output Artifact: run_summary_digit_specialized_validation.json

### Key Metrics

- episodes: 270
- stop_reason: DigitCountingCapabilityBoundary@4Digits
- digit_counting.status: stopped_capability_boundary
- digit_counting.max_verified_digits: 3
- digit_counting.boundary_digits: 4
- digit_counting.samples: 230

### Notes

- Boundary stop now uses sustained strict-gate non-pass at max loops (no fallback-count dependency).
- Result matches specialized simulator profile: exact-capable through 3 digits, boundary discovered at 4 digits.

## Run 030

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 100
- Status: Success
- Output Artifact: training/runs/20260606T093623Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- test_evaluation.contract: training/materials/rlhf_confidence_v1/config/test_contract.json
- test_evaluation.result_json: training/materials/rlhf_confidence_v1/results/20260606T093623Z_rlhf_confidence_v1_test_result.json
- test_evaluation.metrics.samples: 2
- test_evaluation.metrics.accuracy: 0.5
- test_evaluation.passed: false

### Notes

- Test simulation and pass criteria are now loaded from the RLHF material package itself.
- Evidence artifact is written next to the owning test data in material-local results.

## Run 031

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/sft_framework_patterns_v1/config/training_config.json --seed 101 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T093627Z_sft_framework_patterns_v1/run_summary.json

### Key Metrics

- test_evaluation.contract: training/materials/sft_framework_patterns_v1/config/test_contract.json
- test_evaluation.result_json: training/materials/sft_framework_patterns_v1/results/20260606T093627Z_sft_framework_patterns_v1_test_result.json
- test_evaluation.metrics.samples: 1
- test_evaluation.metrics.accuracy: 1.0
- test_evaluation.passed: true

### Notes

- SFT package also uses local simulator + local pass criteria + colocated result artifacts.

## Run 032

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 120 --simulation-mode improving --out run_summary_digit_contract_driven.json
- Status: Success
- Output Artifact: run_summary_digit_contract_driven.json

### Key Metrics

- stop_reason: DigitCountingCapabilityBoundary@4Digits
- digit_counting.contract: training/materials/digit_counting_curriculum_v1/config/test_contract.json
- digit_counting.max_verified_digits: 3
- digit_counting.boundary_digits: 4

### Notes

- DigitCounting curriculum knobs are now loaded from test-local contract instead of hardcoded runtime defaults.

## Run 033

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 120 --simulation-mode improving --out run_summary_digit_contract_driven.json
- Status: Success
- Output Artifact: run_summary_digit_contract_driven.json

### Key Metrics

- stop_reason: DigitCountingCapabilityBoundary@4Digits
- digit_counting.test_id: digit_counting
- digit_counting.contract: training/materials/digit_counting_curriculum_v1/config/test_contract.json
- digit_counting.max_verified_digits: 3
- digit_counting.boundary_digits: 4

### Notes

- Trainer now receives test package root and discovers config/test_contract.json automatically.
- DigitCounting loop controller is now test-owned at training/materials/digit_counting_curriculum_v1/runtime/controller.py.

## Run 034

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 102 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T100215Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- test_evaluation.contract: training/materials/rlhf_confidence_v1/config/test_contract.json
- test_evaluation.metrics.samples: 2
- test_evaluation.metrics.accuracy: 0.5
- test_evaluation.passed: false

### Notes

- RLHF test contract now includes standard self-identification fields (`test_id`, `test_type`, `controller`, `generic`, `test_specific`).
- Pipeline evaluation remains backward-compatible and successful with standardized contract shape.

## Run 035

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 120 --simulation-mode improving --out run_summary_digit_contract_driven.json
- Status: Success
- Output Artifact: run_summary_digit_contract_driven.json

### Key Metrics

- stop_reason: DigitCountingCapabilityBoundary@4Digits
- digit_counting.max_verified_digits: 3
- digit_counting.boundary_digits: 4
- digit_counting.samples: 230

### Notes

- Runtime dispatch is now stage-agnostic through `stage_test_roots` mapping and `--stage-test-root` CLI entries.
- Refactor preserved natural DigitCounting boundary discovery behavior (3 verified, boundary at 4).

## Run 036

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 120 --simulation-mode improving --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --out run_summary_stage_test_only.json
- Status: Success
- Output Artifact: run_summary_stage_test_only.json

### Key Metrics

- stop_reason: DigitCountingCapabilityBoundary@4Digits
- stage_tests.DigitCounting.max_verified_digits: 3
- stage_tests.DigitCounting.boundary_digits: 4
- stage_tests.DigitCounting.samples: 230

### Notes

- Removed generic runtime backward-compatibility branches (`digit_test_root` default and `digit_counting` summary alias).
- Explicit stage mapping remains fully functional and preserves expected DigitCounting capability-boundary behavior.

## Run 037

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 103 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T104947Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- test_evaluation.contract: training/materials/rlhf_confidence_v1/config/test_contract.json
- test_evaluation.metrics.samples: 2
- test_evaluation.metrics.accuracy: 0.5
- test_evaluation.passed: false

### Notes

- Evaluation pipeline now enforces strict contract-v2 fields (`controller`, `generic`, `test_specific`) with no legacy fallback parsing.
- RLHF test contract runs successfully after removing deprecated compatibility keys.

## Run 038

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/sft_framework_patterns_v1/config/training_config.json --seed 104 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T104949Z_sft_framework_patterns_v1/run_summary.json

### Key Metrics

- test_evaluation.contract: training/materials/sft_framework_patterns_v1/config/test_contract.json
- test_evaluation.metrics.samples: 1
- test_evaluation.metrics.accuracy: 1.0
- test_evaluation.passed: true

### Notes

- SFT test contract also runs successfully under strict contract-v2-only evaluation parsing.

## Run 039

- Command: vllm --version
- Status: Failed (environment readiness)

### Notes

- Local shell does not have vLLM command available.

## Run 040

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe -c "import importlib.util;print('vllm_installed=', importlib.util.find_spec('vllm') is not None)"
- Status: Success

### Key Metrics

- vllm_installed: False

### Notes

- Project Python environment currently does not include `vllm` package.

## Run 041

- Command: curl http://127.0.0.1:8000/v1/models
- Status: Failed (endpoint readiness)

### Notes

- No local vLLM OpenAI-compatible server reachable at `127.0.0.1:8000`.

## Run 042

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe main.py --episodes 3 --llm-provider real_vllm --llm-model Qwen/Qwen2.5-0.5B-Instruct --llm-base-url http://127.0.0.1:8000/v1 --simulation-mode improving --out run_summary_vllm_provider_smoke.json
- Status: Success
- Output Artifact: run_summary_vllm_provider_smoke.json

### Key Metrics

- llm_provider.type: real_vllm
- stop_reason: Completed
- episodes: 3

### Notes

- Runtime real_vllm provider path executes end-to-end and fails fast with low-confidence fallback when endpoint is unavailable.
- Real DigitCounting boundary probing requires active vLLM server with tiny Hugging Face model.

## Run 043

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 105 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T120217Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- training_mode: rlhf
- artifacts.ollama.status: conversion_required
- artifacts.ollama.modelfile: training/runs/20260606T120217Z_rlhf_confidence_v1/ollama/Modelfile

### Notes

- RLHF pipeline now emits run-scoped Ollama handoff bundle.
- GGUF not yet present; conversion note generated under run ollama folder.

## Run 044

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/sft_framework_patterns_v1/config/training_config.json --seed 106 --dry-run
- Status: Failed (expected guard)

### Notes

- Pipeline correctly rejects non-RLHF mode with explicit RuntimeError.

## Run 045

- Command: d:/AI/AITraining2/.venv/Scripts/python.exe scripts/run_training_pipeline.py --config training/materials/rlhf_confidence_v1/config/training_config.json --seed 107 --dry-run
- Status: Success
- Output Artifact: training/runs/20260606T120259Z_rlhf_confidence_v1/run_summary.json

### Key Metrics

- training_mode: rlhf
- artifacts.ollama.model_name: stage2-confidence
- artifacts.ollama.status: conversion_required

### Notes

- RLHF dry-run remains healthy after adding RLHF-only guard and Ollama handoff metadata.
