from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.training import ClosedLoopTrainer, TrainerConfig
from src.models import Mode, SimulationMode


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meta-cognitive closed-loop trainer (Phase 0-4)")
    p.add_argument("--episodes", type=int, default=120, help="Total episodes across Stage 0-2")
    p.add_argument("--out", type=str, default="run_summary.json", help="Summary output JSON path")
    p.add_argument(
        "--enable-self-extension",
        action="store_true",
        default=False,
        help="Enable Stage 3-4 self-generated tasks, reward profiles, and curriculum expansion",
    )
    p.add_argument(
        "--self-task-count",
        type=int,
        default=60,
        help="Generated task count for self-extension loop",
    )
    p.add_argument(
        "--simulation-mode",
        type=str,
        default=SimulationMode.IMPROVING.value,
        choices=[SimulationMode.IMPROVING.value, SimulationMode.STUCK.value],
        help="Simulation behavior: improving or stuck",
    )
    p.add_argument(
        "--max-recursion-depth",
        type=int,
        default=2,
        help="Maximum recursive decomposition depth for low-confidence paths",
    )
    p.add_argument(
        "--stage-initial-budget",
        type=float,
        default=100.0,
        help="Initial budget per task stage; lower values force budget-depletion fallback",
    )
    p.add_argument(
        "--mode",
        type=str,
        default=Mode.EXPERT.value,
        choices=[Mode.CHAT.value, Mode.EXPERT.value, Mode.AUDIT.value],
        help="Reasoning mode used for confidence threshold and strictness",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    trainer = ClosedLoopTrainer(
        TrainerConfig(
            episodes=args.episodes,
            enable_self_extension=args.enable_self_extension,
            self_task_count=args.self_task_count,
            mode=Mode(args.mode),
            simulation_mode=SimulationMode(args.simulation_mode),
            max_recursion_depth=args.max_recursion_depth,
            stage_initial_budget=args.stage_initial_budget,
        )
    )
    summary = trainer.run()

    out_path = Path(args.out)
    payload = {
        "episodes": summary["episodes"],
        "total_reward": summary["total_reward"],
        "calibration_error": summary["calibration_error"],
        "false_high_confidence": summary["false_high_confidence"],
        "budget_efficiency": summary["budget_efficiency"],
        "stage_metrics": summary["stage_metrics"],
        "self_extension": summary.get("self_extension", {}),
        "simulation_mode": summary.get("simulation_mode"),
        "stop_reason": summary.get("stop_reason"),
        "fallback_events": summary.get("fallback_events", []),
        "tool_invocations": summary.get("tool_invocations", []),
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== Closed Loop Run Summary ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Summary written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
