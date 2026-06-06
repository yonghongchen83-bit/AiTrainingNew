from __future__ import annotations

import argparse
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Training pipeline orchestrator stub (RLHF/SFT)")
    p.add_argument("--config", type=str, required=True, help="Path to training config json")
    p.add_argument("--seed", type=int, required=True, help="Required fixed seed for reproducibility")
    p.add_argument("--dry-run", action="store_true", default=False, help="Do not create model artifacts")
    return p.parse_args()


def _ensure_relative(path_str: str, root: Path) -> Path:
    p = (root / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str)
    return p


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def _import_function(module_path: Path, function_name: str):
    spec = importlib.util.spec_from_file_location(f"test_module_{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, function_name, None)
    if fn is None:
        raise RuntimeError(f"Function '{function_name}' not found in module: {module_path}")
    return fn


def _evaluate_test_contract(cfg: dict[str, Any], repo_root: Path, seed: int, run_id: str) -> dict[str, Any] | None:
    contract_ref = cfg.get("test_contract")
    if not contract_ref:
        return None

    contract_path = _ensure_relative(contract_ref, repo_root)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    controller_cfg = contract.get("controller")
    if not isinstance(controller_cfg, dict):
        raise RuntimeError("test_contract field 'controller' must be an object")

    simulation_module_ref = controller_cfg.get("module")
    if not simulation_module_ref:
        raise RuntimeError("test_contract.controller.module is required")
    simulation_module = _ensure_relative(str(simulation_module_ref), repo_root)

    simulation_entry = str(controller_cfg.get("entry", "simulate_batch"))
    simulate_batch = _import_function(simulation_module, simulation_entry)

    generic_cfg = contract.get("generic", {})
    if not isinstance(generic_cfg, dict):
        raise RuntimeError("test_contract field 'generic' must be an object")

    specific_cfg = contract.get("test_specific", {})
    if not isinstance(specific_cfg, dict):
        raise RuntimeError("test_contract field 'test_specific' must be an object")

    pass_cfg = specific_cfg.get("pass_conditions", {})
    if not isinstance(pass_cfg, dict):
        raise RuntimeError("test_contract.test_specific.pass_conditions must be an object")

    step_size = int(generic_cfg.get("step_size", 1))
    batch_size = max(1, int(generic_cfg.get("batch_size", 8)))
    required_confidence = float(generic_cfg.get("required_confidence", 0.9))

    test_path = _ensure_relative(cfg["datasets"]["test"], repo_root)
    samples = _load_jsonl(test_path)
    if not samples:
        return {
            "status": "no_test_samples",
            "contract": str(contract_path.relative_to(repo_root)),
        }

    total = 0
    correct_count = 0
    confidence_sum = 0.0
    false_high_conf = 0
    predictions: list[dict[str, Any]] = []

    step_index = 0
    for i in range(0, len(samples), batch_size):
        batch = samples[i : i + batch_size]
        outputs = simulate_batch(
            batch=batch,
            step_index=step_index,
            contract=contract,
            seed=seed + i,
        )

        if len(outputs) != len(batch):
            raise RuntimeError("Simulation output size must equal batch size")

        for sample, out in zip(batch, outputs):
            confidence = float(out.get("confidence", 0.0))
            is_correct = out.get("correct")

            if is_correct is None:
                if "correct" in sample:
                    is_correct = bool(sample["correct"])
                elif "expected_response" in sample:
                    is_correct = str(out.get("response", "")).strip() == str(sample["expected_response"]).strip()
                else:
                    is_correct = True

            total += 1
            correct_count += 1 if is_correct else 0
            confidence_sum += confidence
            if confidence >= required_confidence and not is_correct:
                false_high_conf += 1

            prediction = {
                "prompt": sample.get("prompt"),
                "response": out.get("response"),
                "confidence": confidence,
                "correct": bool(is_correct),
                "step_index": step_index,
            }
            predictions.append(prediction)

        step_index += step_size

    accuracy = correct_count / max(total, 1)
    avg_confidence = confidence_sum / max(total, 1)
    false_high_conf_rate = false_high_conf / max(total, 1)

    min_accuracy = float(pass_cfg.get("min_accuracy", 0.0))
    min_avg_confidence = float(pass_cfg.get("min_avg_confidence", 0.0))
    max_false_high_conf = float(pass_cfg.get("max_false_high_confidence_rate", 1.0))
    passed = (
        accuracy >= min_accuracy
        and avg_confidence >= min_avg_confidence
        and false_high_conf_rate <= max_false_high_conf
    )

    results_cfg = contract.get("results", {})
    output_dir = _ensure_relative(results_cfg.get("output_dir", str(contract_path.parent / "results")), repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_payload = {
        "run_id": run_id,
        "training_id": cfg["training_id"],
        "test_id": contract.get("test_id"),
        "test_type": contract.get("test_type"),
        "test_contract": str(contract_path.relative_to(repo_root)),
        "test_dataset": str(test_path.relative_to(repo_root)),
        "evaluation": {
            "step_size": step_size,
            "batch_size": batch_size,
            "required_confidence": required_confidence,
            "pass_conditions": pass_cfg,
        },
        "metrics": {
            "samples": total,
            "accuracy": round(accuracy, 6),
            "avg_confidence": round(avg_confidence, 6),
            "false_high_confidence_rate": round(false_high_conf_rate, 6),
            "steps_executed": math.ceil(len(samples) / batch_size),
        },
        "passed": passed,
    }

    result_json = output_dir / f"{run_id}_test_result.json"
    result_json.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    predictions_jsonl: str | None = None
    if bool(results_cfg.get("write_jsonl_predictions", True)):
        pred_path = output_dir / f"{run_id}_predictions.jsonl"
        with pred_path.open("w", encoding="utf-8") as f:
            for row in predictions:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        predictions_jsonl = str(pred_path.relative_to(repo_root))

    return {
        "status": "completed",
        "contract": str(contract_path.relative_to(repo_root)),
        "result_json": str(result_json.relative_to(repo_root)),
        "predictions_jsonl": predictions_jsonl,
        "metrics": result_payload["metrics"],
        "passed": passed,
    }


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

    summary["test_evaluation"] = _evaluate_test_contract(
        cfg=cfg,
        repo_root=repo_root,
        seed=args.seed,
        run_id=run_id,
    )

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
