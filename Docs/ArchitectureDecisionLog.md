# Architecture Decision Log

Last Updated: 2026-06-06

## ADR-001: Single Source of Implementation Truth

- Date: 2026-06-06
- Decision: Use AiDevelopmenPlan.txt as the only implementation baseline. Other docs are conceptual support.
- Rationale: User explicitly requested implementation to follow AiDevelopmenPlan only.
- Consequence: Conflicts are resolved in favor of AiDevelopmenPlan.

## ADR-002: Runtime Language

- Date: 2026-06-06
- Decision: Python for current implementation.
- Rationale: User approved Python and requested runnable closed loop.
- Consequence: Initial implementation avoids non-essential external dependencies.

## ADR-003: Scope Boundary for Current Delivery

- Date: 2026-06-06
- Decision: Deliver runnable Stage 0-2 loop; Stage 3-4 only as stubs.
- Rationale: User requested 0-2 sufficient with stubbed self-extension.
- Consequence: No implementation/testing for self-curriculum expansion yet.

## ADR-004: Reward Function Choice

- Date: 2026-06-06
- Decision: Use AiDevelopmenPlan reward as canonical runtime reward.
- Rationale: No true conflict across docs; other formulations are refinements for later experiments.
- Consequence: Keep runtime reward stable and add extension points for future dynamic pressure terms.

## ADR-005: Deterministic Governance Hooks

- Date: 2026-06-06
- Decision: Add workspace hooks in .github/hooks to enforce milestone documentation checks around commit operations.
- Rationale: User requested visible and enforceable governance, not only instruction-level guidance.
- Consequence: Commit-related tool executions are post-validated against required documentation files.

## ADR-006: Strict Milestone Commit Message Prefix

- Date: 2026-06-06
- Decision: Enforce git commit message prefix "milestone:" through PreToolUse hook validation.
- Rationale: Make milestone commits machine-detectable and consistently auditable.
- Consequence: Non-compliant commit commands are denied before execution.

## ADR-007: Milestone Bootstrap Automation

- Date: 2026-06-06
- Decision: Add scripts/start_milestone.py to auto-seed plan, progress, and execution placeholders for each new milestone.
- Rationale: User requested visible progress and persistent governance without manual bookkeeping overhead.
- Consequence: New milestones can start with one command and immediately appear in governance docs.

## ADR-008: Stage 3-4 Deterministic Self-Extension Realization

- Date: 2026-06-06
- Decision: Implement Stage 3 (AI-generated tasks and reward profiles) and Stage 4 (self curriculum expansion) via deterministic planner logic integrated with runtime trainer.
- Rationale: Complete remaining implementation goals while preserving a runnable baseline and auditable behavior.
- Consequence: Closed loop now supports Stage 0-4 execution with expandable tool discovery and generated curriculum stages.

## ADR-009: Canonical Tool Names with Alias Trigger Words

- Date: 2026-06-06
- Decision: Represent each tool with a canonical name plus a list of alias trigger words; resolve aliases at runtime before usage accounting.
- Rationale: User required one tool to support multiple trigger phrases from ColdStartToolBox while preserving deterministic tracking.
- Consequence: Toolbox registration/lookup/usage all operate through alias resolution, and newly generated tools can keep stable canonical identities.

## ADR-010: OpenAI Function Tool-Call Protocol as Runtime Event Output

- Date: 2026-06-06
- Decision: Export tool invocations in standard OpenAI function call shape (`type=function`, `id`, `function.name`, `function.arguments`).
- Rationale: User required protocol-level compatibility and auditable fallback traces.
- Consequence: Runtime summary now includes machine-readable tool-call events for toolsApplication, CompletionFailed, TrainingRequired, and ToolsExtension.

## ADR-011: Explicit Fallback Escalation Paths for Uncertainty and Budget Depletion

- Date: 2026-06-06
- Decision: Add recursive low-confidence handling with bounded depth and emit CompletionFailed events; for irreducible uncertainty also emit TrainingRequired and ToolsExtension; for budget depletion emit CompletionFailed with reason_code BudgetExhausted.
- Rationale: User requested realistic failing/improving branches, recursion abort behavior, and explicit budget-exhausted semantics.
- Consequence: Summary contains structured fallback_events and protocol-compliant tool invocations for both uncertainty and budget failure classes.

## ADR-012: Adaptive Confidence Gate for Improving Mode

- Date: 2026-06-06
- Decision: In improving mode, apply an adaptive confidence threshold and permit bounded low-confidence execution attempts when recursion depth is exhausted.
- Rationale: Fixed a lockup where Expert threshold forced all episodes into irreducible fallback, preventing any learning signal and making improving/stuck behavior indistinguishable.
- Consequence: Improving mode now progresses through execution/reward updates and shows fewer fallbacks than stuck mode under the same episode count.

## ADR-013: Official Swappable LLM Provider Layer

- Date: 2026-06-06
- Decision: Introduce a formal LLM provider contract and factory-based provider selection (`simulated`, `real_stub`) that trainer logic depends on instead of a concrete agent class.
- Rationale: Framework validation must remain possible without real model dependencies, while preserving a clean insertion path for real LLM integration later.
- Consequence: Runtime can swap provider backends by CLI/config; summaries now emit provider metadata for auditability.

## ADR-014: RLHF-First Training Policy with Config-Driven SFT Switch

- Date: 2026-06-06
- Decision: Make RLHF the default training mode for confidence calibration stages; allow SFT switch in later framework-pattern stages via config only.
- Rationale: Current objective emphasizes confidence calibration and reward alignment, while future stages may require supervised pattern shaping.
- Consequence: Training orchestration stays stable while mode changes remain explicit, auditable, and stage-bound.

## ADR-015: Unified Training Workspace Contract

- Date: 2026-06-06
- Decision: Introduce `training/` with standardized subfolders for materials, model artifacts, run outputs, and run registry, plus required controls for best/last retention and human promotion gate.
- Rationale: User requested a concrete filesystem contract where engines load models from a model folder and write trained outputs with summaries.
- Consequence: RLHF/SFT runs now share one storage and governance contract with reproducibility snapshots and append-only run history.
