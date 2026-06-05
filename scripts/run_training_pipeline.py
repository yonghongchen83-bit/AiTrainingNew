from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Training pipeline orchestrator stub (RLHF/SFT)")
    p.add_argument("--config", type=str, required=True, help="Path to training config json")
    p.add_argument("--seed", type=int, required=True, help="Required fixed seed for reproducibility")
    p.add_argument("--dry-run", action="store_true", default=False, help="Do not create model artifacts")
    return p.parse_args()


def _ensure_relative(path_str: str, root: Path) -> Path:
    p = (root / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str)
    return p


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent

    cfg_path = _ensure_relative(args.config, repo_root)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{cfg['training_id']}"
    run_dir = repo_root / "training" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Freeze config snapshot for reproducibility.
    snapshot_path = run_dir / "config_snapshot.json"
    snapshot = dict(cfg)
    snapshot["seed"] = args.seed
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "run_id": run_id,
        "training_id": cfg["training_id"],
        "training_mode": cfg["training_mode"],
        "engine": cfg["engine"],
        "seed": args.seed,
        "status": "dry_run" if args.dry_run else "completed",
        "checkpoint_retention": cfg.get("retention", {}).get("keep", ["best", "last"]),
        "human_approval_required": cfg.get("promotion", {}).get("human_approval_required", True),
        "artifacts": {
            "best": f"training/models/checkpoints/{cfg['output_model_prefix']}.best",
            "last": f"training/models/checkpoints/{cfg['output_model_prefix']}.last",
            "promoted": f"training/models/promoted/{cfg.get('stage', 'stageX')}.end.model",
        },
    }

    if not args.dry_run:
        best_path = repo_root / summary["artifacts"]["best"]
        last_path = repo_root / summary["artifacts"]["last"]
        best_path.parent.mkdir(parents=True, exist_ok=True)
        last_path.parent.mkdir(parents=True, exist_ok=True)
        best_path.write_text("model_artifact_placeholder_best", encoding="utf-8")
        last_path.write_text("model_artifact_placeholder_last", encoding="utf-8")

    summary_path = run_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path = repo_root / "training" / "registry" / "runs_manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Run summary written to: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
