from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


STAGE_CONFIGS = {
    "stage2": "training/materials/rlhf_confidence_v1/config/training_config.json",
    "stage3": "training/materials/sft_framework_patterns_v1/config/training_config.json",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Human-friendly stage training launcher")
    p.add_argument("--stage", required=True, choices=sorted(STAGE_CONFIGS.keys()), help="Stage to train")
    p.add_argument("--seed", required=True, type=int, help="Fixed seed for reproducibility")
    p.add_argument("--dry-run", action="store_true", default=False, help="Run pipeline without writing checkpoint artifacts")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    runner = repo_root / "scripts" / "run_training_pipeline.py"
    config = repo_root / STAGE_CONFIGS[args.stage]

    cmd = [
        sys.executable,
        str(runner),
        "--config",
        str(config),
        "--seed",
        str(args.seed),
    ]
    if args.dry_run:
        cmd.append("--dry-run")

    print(f"[training] launching {args.stage} with seed={args.seed}, dry_run={args.dry_run}")
    print("[training] command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(repo_root), check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
