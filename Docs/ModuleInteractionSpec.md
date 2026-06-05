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

## Future Stub Interfaces (Stage 3-4)

- src.self_extension.SelfExtensionPlanner.generate_tasks
- src.self_extension.SelfExtensionPlanner.generate_reward_functions
- src.self_extension.SelfExtensionPlanner.expand_curriculum
