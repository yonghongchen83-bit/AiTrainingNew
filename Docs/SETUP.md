# Environment & Model Setup for AI

> **Goal:** Reproduce this workspace on any machine without pushing model files to git.
> Models are documented by name and source URL — they download automatically on first run.

---

## 1. Prerequisites

| Dependency | Version | Notes |
|-----------|---------|-------|
| Python | ≥ 3.12 | Tested on 3.12 |
| Git | any | For cloning |
| pip | latest | Bundled with Python |
| (Optional) Ollama | latest | Only if using Ollama backend instead of direct HF |
| (Optional) NVIDIA GPU | T1200+ | 4 GB VRAM minimum; CUDA 12.4+ |

---

## 2. Models Used

| Model | HF ID / Ollama Name | Size | Source | Used By |
|-------|---------------------|------|--------|---------|
| Qwen 2.5 0.5B Instruct | `Qwen/Qwen2.5-0.5B-Instruct` | ~988 MB | [HuggingFace](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | `RealLocalProvider` (direct transformers) |
| Qwen 2.5 0.5B (Ollama) | `qwen2.5:0.5b` | ~397 MB | [Ollama Library](https://ollama.com/library/qwen2.5) | `RealVLLMProvider` (Ollama API) |

> **Note:** Model files are cached automatically to `~/.cache/huggingface/hub/` or
> `~/.ollama/models/`. They are **never committed to git**.

---

## 3. Quick Start (Windows)

```powershell
# 1. Clone
git clone <repo-url> d:\AI\AITraining2
cd d:\AI\AITraining2

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install CPU torch + deps (fast, works everywhere)
pip install torch transformers accelerate

# 4. Run the automated setup
python scripts\setup.py
```

## 3b. Quick Start (Linux / macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch transformers accelerate
python3 scripts/setup.py
```

---

## 4. Optional: GPU (CUDA) Torch

For **~10-50× faster** inference, install CUDA-enabled torch:

```powershell
pip uninstall torch --yes
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

Verify:
```powershell
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
# → CUDA: True
```

---

## 5. Optional: Ollama Backend

```powershell
# Install Ollama from https://ollama.com
ollama pull qwen2.5:0.5b

# Keep ollama running in background
ollama serve
```

---

## 6. Verify Everything Works

```powershell
# Smoke test — simulated provider (no downloads)
python main.py --episodes 3 --out test_smoke.json

# Smoke test — curriculum controller with simulated provider
python main.py --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --episodes 10 --out test_curriculum.json

# Smoke test — real local model (auto-downloads Qwen 0.5B on first run)
python -c "from src.llm_provider import build_llm_provider; from src.models import *; p = build_llm_provider(LLMProviderType.REAL_LOCAL, 42, SimulationMode.IMPROVING, 'Qwen/Qwen2.5-0.5B-Instruct'); out = p.predict('数字 123 一共有几位？', '3', 100.0, Mode.EXPERT, StageConfig(1,'DigitCounting',False,None,False,False)); print(f'OK: answer={out.answer}')"
```

---

## 7. Project Structure (Key Files)

```
AITraining2/
├── AGENTS.md                  # VS Code agent definitions
├── main.py                    # Entry point — training pipeline
├── src/
│   ├── llm_provider.py        # Provider abstraction + all backends
│   ├── training.py            # Closed-loop training orchestrator
│   ├── environment.py         # Math task environment
│   └── models.py              # Data types & enums
├── training/
│   ├── materials/
│   │   └── digit_counting_curriculum_v1/
│   │       ├── config/test_contract.json   # Curriculum parameters
│   │       └── runtime/controller.py        # Boundary detection logic
│   └── scripts/
│       ├── setup.py            # Automated setup checker
│       └── start_training.py   # Pipeline launcher
├── scripts/
│   ├── setup.ps1               # Windows setup script
│   └── setup.sh                # Linux setup script
└── Docs/
    ├── SETUP.md                # This file
    └── TrainingAIMAndStructure.md
```

---

## 8. CI / Headless

The pipeline runs fully headless. No GPU required (CPU mode is slow but works).
All model downloads happen once on first inference and are cached to `~/.cache/`.
