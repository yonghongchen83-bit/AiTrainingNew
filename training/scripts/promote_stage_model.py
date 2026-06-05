from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Human-gated model promotion utility")
    p.add_argument("--run-id", required=True, help="Run id under training/runs/")
    p.add_argument("--stage", required=True, help="Stage name to promote (example: stage2)")
    p.add_argument("--approve", action="store_true", default=False, help="Set to approve promotion")
    p.add_argument("--reason", type=str, default="", help="Human review reason")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]

    run_dir = repo_root / "training" / "runs" / args.run_id
    summary_path = run_dir / "run_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Run summary not found: {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    promoted_path = repo_root / "training" / "models" / "promoted" / f"{args.stage}.end.model"
    promoted_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "record_type": "promotion_decision",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "training_id": summary.get("training_id"),
        "stage": args.stage,
        "approved": bool(args.approve),
        "reason": args.reason,
        "promoted_model": promoted_path.relative_to(repo_root).as_posix(),
    }

    if args.approve:
        promoted_path.write_text(
            f"promoted_from_run={args.run_id}\ntraining_id={summary.get('training_id')}\n",
            encoding="utf-8",
        )

    manifest = repo_root / "training" / "registry" / "runs_manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps(event, ensure_ascii=False, indent=2))
    if args.approve:
        print(f"Promoted model written: {promoted_path}")
    else:
        print("Decision recorded without promotion artifact (approve=false).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
