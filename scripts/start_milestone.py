from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_FILE = ROOT / "Docs" / "ImplementationPlan.md"
PROGRESS_FILE = ROOT / "Docs" / "ImplementationProgress.md"
EXEC_FILE = ROOT / "Docs" / "ExecutionLog.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _append_if_missing(content: str, marker: str, block: str) -> str:
    if marker in content:
        return content
    if not content.endswith("\n"):
        content += "\n"
    return content + "\n" + block


def build_blocks(name: str) -> dict[str, str]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    key = name.strip()

    plan_block = (
        f"- [ ] GOV-AUTO: Bootstrap milestone template for {key}\n"
    )

    progress_block = (
        f"- [ ] Bootstrap milestone: {key}\n"
    )

    exec_block = (
        f"## Milestone Template: {key}\n\n"
        f"- Generated: {now}\n"
        f"- Planned command: git commit -m \"milestone: {key}\"\n"
        f"- Checklist seed:\n"
        f"  - Update Docs/ImplementationPlan.md\n"
        f"  - Update Docs/ImplementationProgress.md\n"
        f"  - Update Docs/ArchitectureDecisionLog.md if architecture changes\n"
        f"  - Update Docs/ModuleInteractionSpec.md if module flow changes\n"
        f"  - Append run evidence in Docs/ExecutionLog.md\n"
    )
    return {"plan": plan_block, "progress": progress_block, "execution": exec_block}


def apply_template(name: str) -> None:
    blocks = build_blocks(name)

    plan = _read(PLAN_FILE)
    progress = _read(PROGRESS_FILE)
    exec_log = _read(EXEC_FILE)

    plan_marker = f"GOV-AUTO: Bootstrap milestone template for {name.strip()}"
    progress_marker = f"Bootstrap milestone: {name.strip()}"
    exec_marker = f"## Milestone Template: {name.strip()}"

    plan = _append_if_missing(plan, plan_marker, blocks["plan"])
    progress = _append_if_missing(progress, progress_marker, blocks["progress"])
    exec_log = _append_if_missing(exec_log, exec_marker, blocks["execution"])

    _write(PLAN_FILE, plan)
    _write(PROGRESS_FILE, progress)
    _write(EXEC_FILE, exec_log)


def print_template(name: str) -> None:
    blocks = build_blocks(name)
    print("=== ImplementationPlan.md entry ===")
    print(blocks["plan"].strip())
    print("\n=== ImplementationProgress.md entry ===")
    print(blocks["progress"].strip())
    print("\n=== ExecutionLog.md entry ===")
    print(blocks["execution"].strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap milestone documentation template")
    parser.add_argument("--name", required=True, help="Milestone short name")
    parser.add_argument("--apply", action="store_true", help="Apply template to Docs files")
    args = parser.parse_args()

    if args.apply:
        apply_template(args.name)
        print(f"Milestone template applied for: {args.name}")
    else:
        print_template(args.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
