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
