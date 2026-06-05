# Module Interaction Spec

Last Updated: 2026-06-06

## Runtime Flow (Stage 0-2)

1. main.py creates TrainerConfig and ClosedLoopTrainer.
2. ClosedLoopTrainer initializes Toolbox and an LLM provider via src.llm_provider.build_llm_provider.
3. For each stage (PlaceValue, DigitCounting, Addition1Digit):
   - MathEnvironment generates one problem.
   - LLM provider predicts structured output (answer/confidence/cost/tool/recursion/background).
   - Toolbox records tool usage if selected.
   - MathEnvironment evaluates success/cost and calls reward.compute_reward.
   - Trainer sends reward signal through provider train_step.
   - Trainer records episode metrics and aggregate statistics.
4. main.py writes run_summary.json and prints metrics.

## Interfaces

- src.llm_provider.LLMProvider.predict(question, expected_answer, budget, mode, stage) -> LLMOutput
- src.llm_provider.LLMProvider.train_step(reward) -> None
- src.llm_provider.build_llm_provider(provider_type, seed, simulation_mode, model_name) -> LLMProvider
- src.environment.MathEnvironment.reset() -> MathProblem
- src.environment.MathEnvironment.step(out, expected_answer, recursion_depth) -> (reward, success, cost)
- src.reward.compute_reward(out, success, actual_cost, stage) -> float
- src.toolbox.Toolbox.query/register/use_tool
- src.training.ClosedLoopTrainer.run() -> summary dict

## Tool Alias and Protocol Interaction Flow

1. src.toolbox.Toolbox stores each tool with canonical `name` and alias `trigger_words`.
2. src.agent.HeuristicLLMAgent may emit alias or canonical trigger words in `LLMOutput.tool_trigger`.
3. src.toolbox.Toolbox.resolve maps alias to canonical name before `use_tool` accounting.
4. src.training.ClosedLoopTrainer emits protocol events in OpenAI function tool-call shape:
   - `type: function`
   - `id: call_<uuid>`
   - `function.name`: one of `toolsApplication`, `CompletionFailed`, `TrainingRequired`, `ToolsExtension`
   - `function.arguments`: JSON string payload

## Fallback and Recursion Escalation Flow

1. Trainer computes confidence threshold by mode (Chat/Expert/Audit).
2. If confidence is below threshold:
   - If a tool exists, trainer emits `toolsApplication` and records tool usage.
   - Otherwise trainer recursively retries with reduced child budget (0.8x), bounded by `max_recursion_depth`.
3. If retries remain unresolved, trainer emits `CompletionFailed` with reason_code `IrreducibleUncertainty` and additionally emits `TrainingRequired` + `ToolsExtension`.
4. If environment budget reaches or drops below zero after step evaluation, trainer emits `CompletionFailed` with reason_code `BudgetExhausted`.
5. Runtime summary exports both `fallback_events` and `tool_invocations` for auditing.

## Future Stub Interfaces (Stage 3-4)

- src.self_extension.SelfExtensionPlanner.generate_tasks
- src.self_extension.SelfExtensionPlanner.generate_reward_functions
- src.self_extension.SelfExtensionPlanner.expand_curriculum

## Governance Interaction Flow

1. Hook file .github/hooks/milestone-governance.json triggers script execution on SessionStart and PostToolUse.
2. scripts/validate_milestone_commit.py reads hook payload from stdin.
3. On SessionStart, script emits governance reminder systemMessage.
4. On PreToolUse, if payload indicates git commit execution, script validates commit message starts with "milestone:".
5. On PostToolUse, if payload indicates git commit execution, script inspects latest commit files.
6. If required docs are missing, script returns block decision with remediation message.

## Milestone Bootstrap Flow

1. scripts/start_milestone.py receives a milestone name.
2. Script appends seed checklist entries into Docs/ImplementationPlan.md and Docs/ImplementationProgress.md.
3. Script appends a milestone template section into Docs/ExecutionLog.md.
4. Governance loop continues with implementation, validation, and milestone commit.

## Self-Extension Runtime Flow (Stage 3-4)

1. src.training.ClosedLoopTrainer completes Stage 0-2 base run.
2. src.self_extension.SelfExtensionPlanner.generate_tasks creates generated task sets for AutoArithmeticS3 and AutoArithmeticS4.
3. src.self_extension.SelfExtensionPlanner.generate_reward_functions derives RewardProfile from calibration error.
4. src.self_extension.SelfExtensionPlanner.expand_curriculum returns StageConfig entries for new stages.
5. src.self_extension.SelfExtensionPlanner.build_toolbox registers discovered tools into src.toolbox.Toolbox.
6. src.training.ClosedLoopTrainer executes generated tasks and scores with src.reward.compute_reward_profile.
7. main.py exports self_extension summary into run output JSON.

## Training Workspace Flow (RLHF/SFT)

1. `scripts/run_training_pipeline.py` reads per-training config from `training/materials/<training_id>/config/training_config.json`.
2. Orchestrator enforces seed presence and writes immutable config snapshot into `training/runs/<run_id>/config_snapshot.json`.
3. Mode is selected by config field `training_mode` (`rlhf` default, `sft` in later pattern stages).
4. Orchestrator writes run summary to `training/runs/<run_id>/run_summary.json`.
5. Best/last checkpoint artifact placeholders are written to `training/models/checkpoints/`.
6. One-line run record is appended to `training/registry/runs_manifest.jsonl`.
7. Promotion to `training/models/promoted/stageN.end.model` is gated by human approval.
