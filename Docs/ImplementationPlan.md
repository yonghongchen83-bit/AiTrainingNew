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

## Runtime Entry Points

- main.py
- src/training.py

## Verification Criteria

- Program runs from command line with no manual patching.
- Summary JSON is written.
- Stage-level metrics are produced.
- Progress and architecture docs are updated after execution.

- [x] GOV-AUTO: Bootstrap milestone template for minimum governance loop
