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
