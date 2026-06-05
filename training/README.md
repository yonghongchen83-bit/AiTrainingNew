# Training Workspace Contract

Last Updated: 2026-06-06

This folder is the official training workspace for both RLHF and SFT workflows.

## Layout

- materials/: Training definitions by training id (for example rlhf_confidence_v1)
- models/: Engine-loadable model artifacts and stage promotion outputs
- runs/: Per-run outputs, summaries, and artifacts
- registry/: Append-only manifest of all training runs

## Mode Policy

- Default mode: RLHF
- SFT is enabled when stage objective switches to framework-pattern learning
- Switching mode must be done by config only; orchestration path remains unchanged

## Retention Policy

- Keep best and last checkpoints only
- Keep run summary and immutable config snapshot for reproducibility
- Human approval is required before promotion to models/promoted

## Human Promotion Gate

If a stage passes human review:
1. Produce stageN.end.model artifact under models/promoted
2. Update next stage config to use that promoted model path as input
3. Record decision in run summary and registry manifest
