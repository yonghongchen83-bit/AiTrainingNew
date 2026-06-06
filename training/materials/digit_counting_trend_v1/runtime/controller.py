"""
Long-run trend test controller.

Runs many episodes at a fixed difficulty level to track whether the model
improves over time (accuracy, confidence, reward trends).
Reports rolling averages at regular intervals.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Callable


DEFAULT_GENERIC: dict[str, Any] = {
    "min_level": 1,
    "max_level": 1,
    "max_total_samples": 10000,
}

DEFAULT_SPECIFIC: dict[str, Any] = {
    "trend_window": 100,
    "report_interval": 100,
    "confidence_pressure_strength": 0.5,
}


def _to_int(cfg: dict[str, Any], key: str, default: int) -> int:
    return int(cfg.get(key, default))


def _to_float(cfg: dict[str, Any], key: str, default: float) -> float:
    return float(cfg.get(key, default))


def run_trend_loop(
    *,
    stage,
    contract: dict[str, Any],
    contract_path: str,
    execute_episode: Callable[..., Any],
    register_capability_summary: Callable[..., str],
) -> dict[str, Any]:
    test_id = str(contract.get("test_id", "digit_counting_trend"))

    generic_cfg = dict(DEFAULT_GENERIC)
    generic_cfg.update(contract.get("generic", {}))

    specific_cfg = dict(DEFAULT_SPECIFIC)
    specific_cfg.update(contract.get("test_specific", {}))

    level = _to_int(generic_cfg, "min_level", 1)
    max_total_samples = _to_int(generic_cfg, "max_total_samples", 10000)
    trend_window = _to_int(specific_cfg, "trend_window", 100)
    report_interval = _to_int(specific_cfg, "report_interval", 100)
    confidence_pressure_strength = _to_float(specific_cfg, "confidence_pressure_strength", 0.5)

    # Rolling windows for trend tracking
    recent_success = deque(maxlen=trend_window)
    recent_confidence = deque(maxlen=trend_window)
    recent_reward = deque(maxlen=trend_window)

    # Full trend data at report intervals
    trend_points: list[dict[str, Any]] = []

    total_reward = 0.0
    total_success = 0

    print(f"\n{'='*70}")
    print(f"TREND TEST — difficulty={level}  max_episodes={max_total_samples}  window={trend_window}")
    print(f"{'='*70}")

    for episode in range(1, max_total_samples + 1):
        record = execute_episode(
            difficulty=level,
            progress_ratio=min(1.0, episode / max_total_samples),
            confidence_pressure_strength=confidence_pressure_strength,
        )

        total_reward += record.reward
        if record.success:
            total_success += 1

        recent_success.append(1 if record.success else 0)
        recent_confidence.append(record.confidence)
        recent_reward.append(record.reward)

        # Report at regular intervals
        if episode % report_interval == 0:
            window_acc = sum(recent_success) / len(recent_success)
            window_conf = sum(recent_confidence) / len(recent_confidence)
            window_reward = sum(recent_reward) / len(recent_reward)
            overall_acc = total_success / episode
            avg_conf_all = (sum(recent_confidence) + (episode - len(recent_confidence)) * 0.0) / episode  # approximate

            trend_points.append({
                "episode": episode,
                "overall_accuracy": round(overall_acc, 4),
                "window_accuracy": round(window_acc, 4),
                "window_avg_confidence": round(window_conf, 4),
                "window_avg_reward": round(window_reward, 4),
                "total_reward": round(total_reward, 4),
            })

            print(
                f"  Episode {episode:5d} | "
                f"acc(last{trend_window})={window_acc:.3f}  "
                f"conf={window_conf:.3f}  "
                f"reward={window_reward:+.3f}  "
                f"| overall acc={overall_acc:.3f}  "
                f"total_reward={total_reward:+.2f}"
            )

    # Final report
    window_acc = sum(recent_success) / len(recent_success)
    window_conf = sum(recent_confidence) / len(recent_confidence)
    window_reward = sum(recent_reward) / len(recent_reward)
    overall_acc = total_success / max_total_samples

    print(f"\n{'─'*70}")
    print(f"COMPLETE — {max_total_samples} episodes at difficulty={level}")
    print(f"  Overall accuracy:     {overall_acc:.4f}")
    print(f"  Final window acc:     {window_acc:.4f}")
    print(f"  Final window conf:    {window_conf:.4f}")
    print(f"  Final window reward:  {window_reward:+.4f}")
    print(f"  Total reward:         {total_reward:+.2f}")
    print(f"{'─'*70}\n")

    tool_name = register_capability_summary(
        test_id=test_id,
        max_verified=total_success,
        boundary=level,
        reason=f"trend_run_complete_{max_total_samples}_episodes",
    )

    summary: dict[str, Any] = {
        "enabled": True,
        "test_id": test_id,
        "status": "completed",
        "contract": contract_path,
        "difficulty_level": level,
        "total_episodes": max_total_samples,
        "overall_accuracy": round(overall_acc, 4),
        "final_window_accuracy": round(window_acc, 4),
        "final_window_confidence": round(window_conf, 4),
        "final_window_reward": round(window_reward, 4),
        "total_reward": round(total_reward, 4),
        "trend_points": trend_points,
        "tool_name": tool_name,
    }

    return {
        "continue_training": False,
        "stop_reason": f"{stage.name}TrendComplete@{max_total_samples}",
        "summary": summary,
    }
