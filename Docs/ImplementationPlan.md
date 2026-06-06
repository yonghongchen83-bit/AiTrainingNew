# Formal Implementation Plan

Last Updated: 2026-06-06

## Delivery Scope

- Baseline: AiDevelopmenPlan.txt
- Runtime Language: Python
- Current Target: Runnable closed loop for Stage 0-4
- Out of Scope in this delivery: Performance tuning and large-model PPO integration

## Work Breakdown with Checkboxes

- [x] P0-01 Define core data models (LLMOutput, StageConfig, metrics, tools)
- [x] P0-02 Build Toolbox with Chinese native trigger words
- [x] P0-03 Build MathEnvironment with Stage 0-2 task generation
- [x] P0-04 Implement canonical reward function from AiDevelopmenPlan
- [x] P1-01 Implement runnable agent interface and structured prediction output
- [x] P1-02 Wire budget/confidence/tool/recursion/background fields
- [x] P2-01 Implement training orchestrator for Stage 0-2 episodes
- [x] P2-02 Export run summary artifact to JSON
- [x] P2-03 Execute end-to-end run to validate close loop
- [x] GIT-01 Initialize local git repository
- [x] GIT-02 Commit Stage 0-2 milestone
- [x] GOV-01 Add workspace governance agent for commit and documentation enforcement
- [x] GIT-03 Commit governance milestone
- [x] GOV-02 Add deterministic workspace hooks for documentation/commit enforcement
- [x] GIT-04 Commit hook governance milestone
- [x] GOV-03 Enforce milestone commit message prefix via PreToolUse hook
- [x] GIT-05 Commit strict commit-message governance milestone
- [x] GOV-04 Add automated milestone bootstrap tool for plan/progress/execution docs
- [x] GIT-06 Commit minimum governance loop automation milestone
- [x] P3-Stub Add self-extension planner stubs only
- [x] P3-Impl Self-generated tasks/reward implementation
- [x] P4-Impl Self curriculum expansion implementation
- [x] GIT-07 Commit Stage 3-4 completion milestone
- [x] P5-01 Upgrade Toolbox to canonical name + multi-trigger alias words
- [x] P5-02 Emit standard OpenAI function tool-call objects in run summary
- [x] P5-03 Add simulation modes (improving/stuck) in heuristic agent
- [x] P5-04 Add recursive low-confidence fallback with CompletionFailed/TrainingRequired/ToolsExtension
- [x] P5-05 Add budget-depletion CompletionFailed path with reason_code=BudgetExhausted
- [x] P5-06 Add runtime CLI controls (mode, recursion depth, stage initial budget)
- [x] P5-07 Validate improving/stuck/budget scenarios and collect artifacts
- [x] GIT-08 Commit protocol + fallback milestone
- [x] P5-08 Fix fallback lockup so improving diverges from stuck
- [x] GIT-09 Commit fallback divergence regression fix
- [x] P6-01 Define official LLM provider contract and factory
- [x] P6-02 Wire trainer to provider abstraction (not concrete simulated class)
- [x] P6-03 Add real-provider runtime stub for future swap-in
- [x] P6-04 Add CLI provider selection and provider metadata in run summary
- [x] P6-05 Document provider architecture and integration path
- [x] GIT-10 Commit provider abstraction milestone
- [x] P7-01 Create official training workspace scaffold under training/
- [x] P7-02 Add RLHF-first and SFT switchable training material templates
- [x] P7-03 Add run registry and reproducible config snapshot flow
- [x] P7-04 Add orchestration stub for mode-driven training execution
- [x] P7-05 Document RLHF-to-SFT switch policy and retention/promotion controls
- [x] GIT-11 Commit training workspace and mode-switch policy milestone
- [x] P8-01 Add human-friendly stage launch scripts under training/scripts
- [x] P8-02 Add human-gated promotion decision utility
- [x] P8-03 Document operator commands for stage execution and promotion
- [x] GIT-12 Commit training operator scripts milestone
- [x] P9-01 Document reusable training AIM and dynamic capability-boundary structure
- [x] P9-02 Implement unified train+eval curriculum loop for DigitCounting with tolerance=0 gate
- [x] P9-03 Implement progressRatio confidence-pressure reward path
- [x] P9-04 Implement global stop logic: capability boundary or requirement reached
- [x] P9-05 Emit DigitCounting capability summary tool metadata in run summary
- [x] P9-06 Execute validation run for DigitCounting curriculum loop
- [x] P10-01 Add test-local simulation module contract per training material
- [x] P10-02 Add per-test evaluation contract with step size, batch size, required confidence, and pass conditions
- [x] P10-03 Write test result evidence artifacts into each test material folder
- [x] P10-04 Validate RLHF and SFT configs with contract-driven test evaluation flow
- [x] P11-01 Add dedicated DigitCounting test-local contract for curriculum parameters
- [x] P11-02 Load DigitCounting curriculum knobs from contract in runtime trainer
- [x] P11-03 Add runtime CLI contract path for DigitCounting contract override
- [x] P11-04 Validate run summary exports active DigitCounting contract path
- [x] P12-01 Define standard self-contained test contract structure (test_id/controller/generic/test_specific)
- [x] P12-02 Update DigitCounting contract to standard structure and add test-owned runtime controller
- [x] P12-03 Refactor trainer to discover test contract from test root folder and dispatch controller generically
- [x] P12-04 Remove DigitCounting-specific contract parsing and gate logic from generic trainer
- [x] P12-05 Validate standardized contract compatibility in training pipeline evaluator
- [x] P13-01 Generalize runtime stage dispatch from hardcoded DigitCounting to configurable stage_test_roots mapping
- [x] P13-02 Add generic CLI stage mapping input (--stage-test-root StageName=path)
- [x] P13-03 Validate generalized dispatch preserves DigitCounting natural capability boundary result (3 verified / 4 boundary)
- [x] P14-01 Remove `digit_test_root` backward-compatibility default from generic trainer config
- [x] P14-02 Remove `--digit-test-root` compatibility CLI argument in favor of explicit `--stage-test-root` mapping
- [x] P14-03 Remove legacy `digit_counting` summary alias; expose test-controller output via `stage_tests` only
- [x] P14-04 Validate explicit mapping path still reaches DigitCounting boundary result (3 verified / 4 boundary)
- [x] P15-01 Remove evaluation-pipeline fallback parsing for legacy contract fields (`simulation_module`, `simulation_entry`, `evaluation.*`)
- [x] P15-02 Enforce strict evaluation contract-v2 schema (`controller` + `generic` + `test_specific`)
- [x] P15-03 Remove legacy compatibility fields from RLHF/SFT test contracts
- [x] P15-04 Validate RLHF and SFT dry-runs succeed with strict contract-v2-only evaluation flow

## Runtime Entry Points

- main.py
- src/training.py

## Verification Criteria

- Program runs from command line with no manual patching.
- Summary JSON is written.
- Stage-level metrics are produced.
- Progress and architecture docs are updated after execution.

- [x] GOV-AUTO: Bootstrap milestone template for minimum governance loop
