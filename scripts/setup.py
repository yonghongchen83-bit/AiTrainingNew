#!/usr/bin/env python3
"""
Automated environment checker & setup helper.
Run after cloning the repo on a new machine:
    python scripts/setup.py
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def check(step: str, ok: bool, detail: str = "") -> None:
    mark = "✓" if ok else "✗"
    print(f"  [{mark}] {step}  {detail}")
    return ok


def main() -> int:
    print("=" * 60)
    print("  AITraining2 — Environment Check")
    print("=" * 60)
    print()

    errors = 0

    # 1. Python version
    py_ver = sys.version_info
    ok = py_ver >= (3, 10)
    check("Python 3.10+", ok, f"({py_ver.major}.{py_ver.minor})")
    if not ok:
        errors += 1

    # 2. Virtual environment
    in_venv = sys.prefix != sys.base_prefix
    check("Virtual environment active", in_venv)
    if not in_venv:
        print("       ⚠ Run: .venv\\Scripts\\Activate.ps1 (Windows) or source .venv/bin/activate")

    # 3. Core dependencies
    deps = [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("accelerate", "accelerate"),
    ]
    for name, pkg in deps:
        try:
            mod = importlib.import_module(pkg)
            ver = getattr(mod, "__version__", "?")
            # Check CUDA
            cuda = ""
            if name == "torch":
                cuda_avail = getattr(mod, "cuda", None) and mod.cuda.is_available()
                cuda = f"  CUDA={cuda_avail}"
            check(f"{name}", True, f"{ver}{cuda}")
        except ImportError:
            check(f"{name}", False, "NOT INSTALLED")
            errors += 1

    # 4. Project module imports
    try:
        from src.models import LLMProviderType, Mode, SimulationMode
        from src.llm_provider import build_llm_provider
        p = build_llm_provider(LLMProviderType.SIMULATED, 42, SimulationMode.IMPROVING)
        check("src.llm_provider (simulated)", True, f"OK")
    except Exception as e:
        check("src.llm_provider (simulated)", False, str(e))
        errors += 1

    try:
        from src.llm_provider import RealLocalProvider
        check("src.llm_provider (RealLocalProvider)", True)
    except Exception as e:
        check("src.llm_provider (RealLocalProvider)", False, str(e))
        errors += 1

    # 5. Curriculum contract exists
    contract = REPO_ROOT / "training" / "materials" / "digit_counting_curriculum_v1" / "config" / "test_contract.json"
    check("DigitCounting curriculum contract", contract.exists())

    # 6. Test run (simulated, 2 episodes)
    print()
    print("  Running smoke test (2 episodes, simulated)...")
    result = subprocess.run(
        [sys.executable, "main.py", "--episodes", "2", "--out", "test_setup_smoke.json"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        check("Smoke test (simulated)", True)
    else:
        check("Smoke test (simulated)", False, result.stderr[:200])
        errors += 1

    # 7. Summary
    print()
    print("=" * 60)
    if errors == 0:
        print("  All checks passed. Environment is ready.")
    else:
        print(f"  {errors} issue(s) found. See messages above.")
    print("=" * 60)

    return errors


if __name__ == "__main__":
    sys.exit(main())
