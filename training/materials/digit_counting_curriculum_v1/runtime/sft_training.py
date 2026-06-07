"""SFT warmup section — runs N episodes at fixed difficulty with SFT mode."""

from __future__ import annotations

from typing import Any, Callable

from src.models import EpisodeRecord
from src.training_type import _to_int, _to_float


class SftTraining:
    """SFT warmup: trains the model on correct answers at specified levels."""

    def __init__(self, section_cfg: dict[str, Any]) -> None:
        self._levels: list[dict[str, int]] = []
        levels_raw = section_cfg.get("levels")
        if isinstance(levels_raw, list):
            for entry in levels_raw:
                if isinstance(entry, dict):
                    lvl = _to_int(entry, "level", 1)
                    ep = _to_int(entry, "episodes", 10)
                    if ep > 0:
                        self._levels.append({"level": lvl, "episodes": ep})
        else:
            # Single-level fallback
            ep = _to_int(section_cfg, "episodes", 10)
            lvl = _to_int(section_cfg, "level", 1)
            if ep > 0:
                self._levels.append({"level": lvl, "episodes": ep})

        self._confidence_pressure_strength = _to_float(
            section_cfg, "confidence_pressure_strength", 0.5
        )

    def run(
        self,
        *,
        execute_episode: Callable[..., EpisodeRecord],
        register_capability_summary: Callable[..., str],
        test_id: str,
        stage_name: str,
    ) -> dict[str, Any]:
        _ = (register_capability_summary, test_id, stage_name)
        total_episodes = 0
        total_success = 0
        level_results: list[dict[str, Any]] = []

        print(f"\n{'='*70}")
        print("SFT WARMUP")
        print(f"{'='*70}")

        for entry in self._levels:
            lvl = entry["level"]
            ep = entry["episodes"]
            lvl_success = 0

            print(f"  Level {lvl} — {ep} episodes ...")
            for i in range(ep):
                progress_ratio = (i + 1) / max(1, ep)
                record = execute_episode(
                    difficulty=lvl,
                    progress_ratio=progress_ratio,
                    confidence_pressure_strength=self._confidence_pressure_strength,
                    training_mode="sft",
                )
                total_episodes += 1
                if bool(record.success):
                    lvl_success += 1
                    total_success += 1
                if (i + 1) % 10 == 0 or i == ep - 1:
                    print(f"    [{i+1}/{ep}] acc={lvl_success}/{i+1}")

            level_results.append({
                "level": lvl,
                "episodes": ep,
                "success_count": lvl_success,
                "accuracy": round(lvl_success / max(1, ep), 4),
            })
            print(f"  Level {lvl} done — {lvl_success}/{ep} ({round(lvl_success/max(1,ep)*100,1)}%)\n")

        print(f"SFT END — {total_success}/{total_episodes} (accuracy {round(total_success/max(1,total_episodes)*100,1)}%)\n")

        return {
            "phase_type": "sft",
            "level_results": level_results,
            "total_episodes": total_episodes,
            "total_success": total_success,
            "overall_accuracy": round(total_success / max(1, total_episodes), 4),
        }
