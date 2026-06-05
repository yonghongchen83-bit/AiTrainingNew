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
