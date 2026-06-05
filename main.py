from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.training import ClosedLoopTrainer, TrainerConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meta-cognitive closed-loop trainer (Phase 0-2)")
    p.add_argument("--episodes", type=int, default=120, help="Total episodes across Stage 0-2")
    p.add_argument("--out", type=str, default="run_summary.json", help="Summary output JSON path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    trainer = ClosedLoopTrainer(TrainerConfig(episodes=args.episodes))
    summary = trainer.run()

    out_path = Path(args.out)
    payload = {
        "episodes": summary["episodes"],
        "total_reward": summary["total_reward"],
        "calibration_error": summary["calibration_error"],
        "false_high_confidence": summary["false_high_confidence"],
        "budget_efficiency": summary["budget_efficiency"],
        "stage_metrics": summary["stage_metrics"],
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== Closed Loop Run Summary ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Summary written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
