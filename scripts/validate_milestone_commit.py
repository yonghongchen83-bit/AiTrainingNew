from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PROGRESS = "Docs/ImplementationProgress.md"
DOC_CHANGE_OPTIONS = {
    "Docs/ExecutionLog.md",
    "Docs/ImplementationPlan.md",
    "Docs/ArchitectureDecisionLog.md",
    "Docs/ModuleInteractionSpec.md",
}


def _read_hook_input() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return {"_raw": data}
    except json.JSONDecodeError:
        return {"_raw_text": raw}


def _as_text(data: dict) -> str:
    try:
        return json.dumps(data, ensure_ascii=False).lower()
    except Exception:
        return str(data).lower()


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return cp.stdout.strip()


def _latest_commit_files() -> set[str]:
    out = _run_git(["show", "--name-only", "--pretty=", "HEAD"])
    files = [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]
    return set(files)


def _session_start_message() -> dict:
    return {
        "continue": True,
        "systemMessage": (
            "Milestone governance active: update Docs/ImplementationProgress.md checkbox status, "
            "document architecture/module interaction changes when applicable, "
            "and create a milestone commit after completion."
        ),
    }


def _post_tool_decision(payload: dict) -> dict:
    blob = _as_text(payload)

    # Only enforce when a git commit was executed through a tool call.
    if "git commit" not in blob:
        return {"continue": True}

    files = _latest_commit_files()
    has_progress = REQUIRED_PROGRESS in files
    has_other_doc = any(doc in files for doc in DOC_CHANGE_OPTIONS)

    if has_progress and has_other_doc:
        return {
            "continue": True,
            "systemMessage": "Milestone commit check passed: required governance docs were included.",
        }

    missing_parts = []
    if not has_progress:
        missing_parts.append(REQUIRED_PROGRESS)
    if not has_other_doc:
        missing_parts.append("one of: " + ", ".join(sorted(DOC_CHANGE_OPTIONS)))

    return {
        "decision": "block",
        "continue": False,
        "stopReason": "Milestone commit governance check failed",
        "systemMessage": (
            "Latest commit is missing required documentation updates: "
            + "; ".join(missing_parts)
            + ". Add docs and commit again with a milestone message."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, choices=["SessionStart", "PostToolUse"])
    args = parser.parse_args()

    payload = _read_hook_input()

    if args.event == "SessionStart":
        print(json.dumps(_session_start_message(), ensure_ascii=False))
        return 0

    print(json.dumps(_post_tool_decision(payload), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
