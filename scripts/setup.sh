#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== AITraining2 Setup ==="

# 1. Python version
PY_VER=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
echo "[1/5] $PY_VER"

# 2. Virtual environment
if [ ! -d .venv ]; then
    echo "[2/5] Creating .venv..."
    python3 -m venv .venv 2>/dev/null || python -m venv .venv
else
    echo "[2/5] .venv already exists"
fi

# Activate
source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true

# 3. Install torch (CPU)
echo "[3/5] Installing torch (CPU)..."
pip install torch --default-timeout=120

# 4. Install remaining
echo "[4/5] Installing transformers + accelerate..."
pip install transformers accelerate --default-timeout=120

# 5. Verify
echo "[5/5] Verification..."
python3 -c "
import torch, transformers, accelerate
print(f'  torch        {torch.__version__}  (CUDA: {torch.cuda.is_available()})')
print(f'  transformers {transformers.__version__}')
print(f'  accelerate   {accelerate.__version__}')
"

python3 -c "
from src.models import LLMProviderType, Mode, SimulationMode
from src.llm_provider import build_llm_provider
p = build_llm_provider(LLMProviderType.SIMULATED, 42, SimulationMode.IMPROVING)
print(f'  SimulatedProvider OK')
"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  python main.py --episodes 3 --out test_smoke.json"
echo "  python main.py --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --episodes 10 --out test_curriculum.json"
echo ""
echo "For GPU (CUDA):  pip uninstall torch --yes && pip install torch --index-url https://download.pytorch.org/whl/cu124"
echo ""
echo "Models (auto-download):"
echo "  - Qwen/Qwen2.5-0.5B-Instruct  from HuggingFace"
