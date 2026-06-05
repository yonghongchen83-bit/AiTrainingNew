# Training Mode Switch Policy

Last Updated: 2026-06-06

## Objective

Define how training mode transitions from RLHF-first confidence calibration stages to SFT framework-pattern stages without changing orchestration contracts.

## Policy

1. Default mode is RLHF for confidence-oriented stages.
2. SFT is allowed when stage objective changes to framework-pattern learning.
3. Switching mode must occur by config only (`training_mode`), not by changing pipeline code path.
4. Retention remains unchanged across modes: keep best and last checkpoints.
5. Human approval is required for promotion to `stageN.end.model`.
6. Reproducibility is mandatory in all modes: fixed seed and frozen config snapshot.

## Switch Criteria

A stage is eligible to switch from RLHF to SFT when:

1. Human review confirms confidence behavior is acceptable for the current stage objective.
2. Calibration and failure analysis indicate reward objective is no longer the primary bottleneck.
3. Next stage objective explicitly requires stable framework-pattern imitation.

## Promotion Flow

1. Execute training run and produce run summary under `training/runs/<run_id>/run_summary.json`.
2. Human reviewer decides approve/reject for stage promotion.
3. On approval, create promoted model artifact under `training/models/promoted/stageN.end.model`.
4. Update next stage config `input_model` to point to promoted artifact.
5. Append decision and artifact path to run registry manifest.
