# Execution Log

Last Updated: 2026-06-06

## Run 001

- Command: python main.py --episodes 120 --out run_summary.json
- Status: Success
- Output Artifact: run_summary.json

### Key Metrics

- episodes: 120
- total_reward: -134.2747
- calibration_error: 0.4407
- false_high_confidence: 0
- budget_efficiency: 1.0

### Stage Metrics

- PlaceValue: success_rate=0.35, mean_surprise=0.499, episodes=40
- DigitCounting: success_rate=0.125, mean_surprise=0.4265, episodes=40
- Addition1Digit: success_rate=0.05, mean_surprise=0.3966, episodes=40

### Notes

- This is a runnable closed loop baseline, not tuned performance.
- Current agent is heuristic and reward-driven; results establish execution validity.
