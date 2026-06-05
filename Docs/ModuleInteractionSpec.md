# Module Interaction Spec

Last Updated: 2026-06-06

## Runtime Flow (Stage 0-2)

1. main.py creates TrainerConfig and ClosedLoopTrainer.
2. ClosedLoopTrainer initializes Toolbox and HeuristicLLMAgent.
3. For each stage (PlaceValue, DigitCounting, Addition1Digit):
   - MathEnvironment generates one problem.
   - Agent predicts structured output (answer/confidence/cost/tool/recursion/background).
   - Toolbox records tool usage if selected.
   - MathEnvironment evaluates success/cost and calls reward.compute_reward.
   - Trainer updates agent skill using reward signal.
   - Trainer records episode metrics and aggregate statistics.
4. main.py writes run_summary.json and prints metrics.

## Interfaces

- src.agent.HeuristicLLMAgent.predict(question, expected_answer, budget, mode, stage) -> LLMOutput
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
