# Training AIM and Reusable Curriculum Structure

Last Updated: 2026-06-06

## Training AIM

The framework trains and evaluates the model in one continuous loop to answer three questions for each stage:

1. What is the model's current capability boundary for this task?
2. Can the model improve under reward pressure when it is not yet fully capable?
3. When should training stop because either:
   - capability upper bound has been identified, or
   - human-defined practical requirement is already satisfied?

This keeps the runtime aligned with the core goals:

- Confidence calibration (`confidence` vs actual correctness)
- Resource/cost awareness (`estimated_cost` vs actual cost)
- Tool awareness and explicit fallback behavior
- Auditable stop decisions

## Reusable Stage Template

Each training stage uses the same control loop with stage-specific task generation and optional tool checks.

### 1) Dynamic Difficulty Level

- Start from minimum level (for DigitCounting: 1 digit).
- Generate tasks at the current level only.
- Keep feeding tasks continuously; there is no hard separation between "train phase" and "eval phase".

### 2) Unified Online Train + Eval

For each sample:

1. Generate one task for current level.
2. Ask model for answer, confidence, estimated cost, and tool usage signals.
3. Compute reward from correctness/surprise/cost and stage rules.
4. Apply training update immediately.
5. Record sample into rolling windows and stage metrics.

### 3) Strict Capability Gate (Tolerance = 0)

For gate window size `N` (default 10):

- Level passes only if all `N` samples are correct.
- Level passes only if all `N` samples have confidence exactly `1.0`.

No tolerance is applied in this stage contract.

### 4) Progress Pressure (progressRatio)

If the model is not yet passing a level, apply confidence pressure that increases with time spent on this level.

$$
progressRatio = min(1.0, levelLoops / targetLoopsAtLevel)
$$

$$
confidencePressure = (1 - confidence) * progressRatio * pressureStrength
$$

Reward subtracts this pressure term. This explicitly pushes the model away from prolonged low-confidence behavior.

### 5) Capability-Boundary Stop

If after enough loops at current level:

- strict pass gate is still not satisfied,

then stop the full simulation and mark this level as outside capability boundary.

### 6) Practical Requirement Stop

If human-defined max requirement is satisfied, stop early.

For DigitCounting, max requirement is `20` digits.

### 7) Tool Capability Summary

On stop (boundary or requirement reached), register a capability-summary tool entry so downstream stages can reuse known boundary facts.

## DigitCounting Instantiation

### Stage Parameters

- Start level: 1 digit
- Max requirement: 20 digits
- Gate window: 10
- Tolerance: 0
- Target loops at level: `baseTargetLoops * level` (default base = 40)
- Max loops per level (boundary check): default 200
- Boundary decision: sustained strict-gate non-pass at max loops

### Stop Reasons

- `DigitCountingRequirementReached@20Digits`
- `DigitCountingCapabilityBoundary@<level>Digits`

### Reuse by Other Stages

Other stages reuse this template by replacing:

- task generator (how difficulty maps to tasks)
- stage-specific reward additives
- stage-specific gate condition (still supports tolerance = 0 if required)
- max requirement definition
- boundary thresholds

The training controller remains the same.