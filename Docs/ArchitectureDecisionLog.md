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

## ADR-016: Operator-Friendly Stage Launch and Promotion Scripts

- Date: 2026-06-06
- Decision: Add human-friendly stage launcher scripts and an explicit promotion decision utility under `training/scripts`.
- Rationale: Reduce operator friction for stage-targeted execution while preserving human-gated promotion requirements.
- Consequence: Users can start stage-specific training and record promotion approval/rejection without editing command internals.

## ADR-017: Unified Stage Curriculum Controller with Capability-Boundary Stops

- Date: 2026-06-06
- Decision: Introduce a reusable curriculum control loop that combines training and evaluation online, applies progressRatio confidence pressure, and stops globally when either capability boundary is determined or human max requirement is reached.
- Rationale: User requested the same training structure be reusable across stages and explicitly separated per-task fallback from trainer-level stop decisions.
- Consequence: DigitCounting now runs as a dynamic level-based curriculum (1..20 digits) with strict gate tolerance=0 and exports capability summary metadata for reuse by later stages.

## ADR-018: Capability Boundary by Sustained Strict-Gate Non-Pass

- Date: 2026-06-06
- Decision: Refine DigitCounting boundary determination to stop on sustained strict-gate non-pass at max loops, without requiring fallback-count thresholds.
- Rationale: Specialized simulator profiles may fail strict gate due to confidence/accuracy limits while producing few fallback events; trainer must still discover boundary naturally.
- Consequence: Boundary detection is now robust for fixed-capability simulators and aligns with expected result patterns (for the current profile: verify 1-3 digits, boundary at 4).

## ADR-019: Test-Local Simulation and Evaluation Contract

- Date: 2026-06-06
- Decision: Move simulation behavior and evaluation criteria into each training material package using `config/test_contract.json` + `simulation/simulator.py`, and write test evidence to material-local `results/`.
- Rationale: As test count grows, centralizing all simulation/test logic in one agent/module becomes hard to maintain and auditable evidence should live with the owning test data.
- Consequence: Each test can independently define step size, batch size, required confidence, and pass conditions while producing colocated artifacts that support or invalidate claims.

## ADR-020: DigitCounting Curriculum Parameters Must Be Test-Contract Driven

- Date: 2026-06-06
- Decision: Remove hardcoded DigitCounting curriculum knobs from trainer defaults and load them from a test-local contract file.
- Rationale: User required DigitCounting curriculum behavior to live with the owning test contract rather than runtime hardcoded values.
- Consequence: Runtime now reads `training/materials/digit_counting_curriculum_v1/config/test_contract.json` and records the active contract path in `digit_counting.contract` run summary output.

## ADR-021: Self-Contained Test Package Contract with Controller Dispatch

- Date: 2026-06-06
- Decision: Standardize each test package to self-identify (`test_id`) and provide its own loop controller (`controller.module` + `controller.entry`), while engine receives only test-folder path and dispatches generically.
- Rationale: User required test-specific loop control and stop decisions to remain inside the owning test folder, with parent runtime remaining test-agnostic.
- Consequence: `src/training.py` now discovers `config/test_contract.json` from test root, imports test controller dynamically, and delegates stage loop execution through test-owned runtime code.

## ADR-022: Stage-to-Test Mapping for Runtime Controller Dispatch

- Date: 2026-06-06
- Decision: Replace stage-name hardcoding with configurable stage-to-test-root mapping (`stage_test_roots`) and remove backward-compatibility defaults from the generic runtime.
- Rationale: Runtime should scale to additional self-contained tests without modifying core stage dispatch logic for each new test.
- Consequence: Trainer now routes only explicitly configured stages through generic controller dispatch, and run summary exposes only `stage_tests` for test-controller outputs.

## ADR-023: Strict Contract-v2 Evaluation Pipeline (No Legacy Fallback)

- Date: 2026-06-06
- Decision: Remove legacy fallback parsing in `scripts/run_training_pipeline.py` and require evaluation contracts to define `controller`, `generic`, and `test_specific` directly.
- Rationale: Generic engine/pipeline should not carry compatibility branches once standardized contract structure is established.
- Consequence: RLHF/SFT evaluation contracts no longer include deprecated `simulation_module`, `simulation_entry`, or `evaluation` duplicates; pipeline fails fast on schema violations.

## ADR-024: Runtime Real Provider Path Uses vLLM OpenAI-Compatible Endpoint

- Date: 2026-06-06
- Decision: Introduce `real_vllm` runtime provider that calls a Hugging Face model served through vLLM OpenAI-compatible API (`/v1/chat/completions`).
- Rationale: User requested real-model capability probing for DigitCounting boundary with tiny model substitution while preserving generic test-controller architecture.
- Consequence: `main.py` now supports `--llm-provider real_vllm` and `--llm-base-url`; runtime can probe real-model behavior when vLLM service is available, while failing fast when endpoint is unavailable.

## ADR-025: RLHF-Only Orchestrator Slice with Ollama Handoff Bundle

- Date: 2026-06-06
- Decision: Restrict `scripts/run_training_pipeline.py` to `training_mode=rlhf` and generate a run-scoped Ollama bundle (`Modelfile` + GGUF pointer/copy state) under `training/runs/<run_id>/ollama/`.
- Rationale: User explicitly requested to ignore SFT for this phase and to save/load the resulting model through Ollama.
- Consequence: Non-RLHF configs now fail fast in this orchestrator path; each RLHF run emits explicit Ollama create/run commands and conversion-required evidence when GGUF is not yet present.
