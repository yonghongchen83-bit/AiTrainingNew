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
