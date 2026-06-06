from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.training import ClosedLoopTrainer, TrainerConfig
from src.models import LLMProviderType, Mode, SimulationMode, TrainingMode


def _parse_stage_test_roots(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in pairs:
        if "=" not in raw:
            raise ValueError(f"Invalid --stage-test-root format: {raw}. Expected StageName=path")
        stage_name, test_root = raw.split("=", 1)
        stage_name = stage_name.strip()
        test_root = test_root.strip()
        if not stage_name or not test_root:
            raise ValueError(f"Invalid --stage-test-root value: {raw}. Expected StageName=path")
        mapping[stage_name] = test_root
    return mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Meta-cognitive closed-loop trainer (Phase 0-4)")
    p.add_argument("--episodes", type=int, default=120, help="Total episodes across Stage 0-2")
    p.add_argument("--out", type=str, default="output/run_summary.json", help="Summary output JSON path")
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
    p.add_argument(
        "--llm-provider",
        type=str,
        default=LLMProviderType.SIMULATED.value,
        choices=[
            LLMProviderType.SIMULATED.value,
            LLMProviderType.REAL_STUB.value,
            LLMProviderType.REAL_VLLM.value,
            LLMProviderType.REAL_LOCAL.value,
        ],
        help="LLM provider backend: simulated, real_stub, real_vllm, or real_local",
    )
    p.add_argument(
        "--llm-model",
        type=str,
        default="gpt-5.3-codex",
        help="Model name metadata for LLM provider (used by real_stub and future real provider)",
    )
    p.add_argument(
        "--llm-base-url",
        type=str,
        default=None,
        help="OpenAI-compatible base URL for real_vllm provider (default: http://127.0.0.1:8000/v1)",
    )
    p.add_argument(
        "--stage-test-root",
        action="append",
        default=[],
        help="Generic stage test root mapping in the form StageName=path (repeatable)",
    )
    p.add_argument(
        "--dumb-mode",
        action="store_true",
        default=False,
        help="Make test simulator always fail — verify early termination",
    )
    p.add_argument(
        "--training-mode",
        type=str,
        default="rlhf",
        choices=["rlhf", "sft"],
        help="Training mode for real model providers: rlhf (reward-weighted) or sft (supervised on correct answer)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    stage_test_roots = _parse_stage_test_roots(args.stage_test_root)
    trainer = ClosedLoopTrainer(
        TrainerConfig(
            episodes=args.episodes,
            enable_self_extension=args.enable_self_extension,
            self_task_count=args.self_task_count,
            mode=Mode(args.mode),
            simulation_mode=SimulationMode(args.simulation_mode),
            llm_provider_type=LLMProviderType(args.llm_provider),
            llm_model_name=args.llm_model,
            llm_base_url=args.llm_base_url,
            max_recursion_depth=args.max_recursion_depth,
            stage_initial_budget=args.stage_initial_budget,
            stage_test_roots=stage_test_roots,
            dumb_mode=args.dumb_mode,
            training_mode=TrainingMode(args.training_mode),
        )
    )
    summary = trainer.run()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "episodes": summary["episodes"],
        "total_reward": summary["total_reward"],
        "calibration_error": summary["calibration_error"],
        "false_high_confidence": summary["false_high_confidence"],
        "budget_efficiency": summary["budget_efficiency"],
        "stage_metrics": summary["stage_metrics"],
        "self_extension": summary.get("self_extension", {}),
        "llm_provider": summary.get("llm_provider", {}),
        "simulation_mode": summary.get("simulation_mode"),
        "stop_reason": summary.get("stop_reason"),
        "stage_tests": summary.get("stage_tests", {}),
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
