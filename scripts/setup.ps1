<#
.SYNOPSIS
    Set up the AITraining2 workspace environment from scratch on a new machine.
.DESCRIPTION
    - Creates virtual environment
    - Installs Python dependencies (CPU torch by default; use -Cuda for GPU)
    - Verifies imports
    - Runs a smoke test
.PARAMETER Cuda
    Install CUDA-enabled torch instead of CPU torch.
.EXAMPLE
    .\scripts\setup.ps1
    .\scripts\setup.ps1 -Cuda
#>

param([switch]$Cuda)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "=== AITraining2 Setup ===" -ForegroundColor Cyan
Write-Host ""

# ---- 1. Python version check ----
$py = (python --version)
Write-Host "[1/5] $py" -ForegroundColor Green
if (-not ($py -match "3\.(1[2-9]|[2-9]\d)")) {
    Write-Warning "Python 3.12+ recommended. Found: $py"
}

# ---- 2. Virtual environment ----
if (-not (Test-Path ".venv")) {
    Write-Host "[2/5] Creating .venv..." -ForegroundColor Green
    python -m venv .venv
} else {
    Write-Host "[2/5] .venv already exists" -ForegroundColor Yellow
}

# Activate
. .\.venv\Scripts\Activate.ps1

# ---- 3. Install torch ----
Write-Host "[3/5] Installing torch..." -ForegroundColor Green
if ($Cuda) {
    pip install torch --index-url https://download.pytorch.org/whl/cu124 --default-timeout=300
} else {
    pip install torch --default-timeout=120
}

# ---- 4. Install remaining dependencies ----
Write-Host "[4/5] Installing transformers + accelerate..." -ForegroundColor Green
pip install transformers accelerate --default-timeout=120

# ---- 5. Verify ----
Write-Host "[5/5] Verification..." -ForegroundColor Green

python -c "
import torch, transformers, accelerate
print(f'  torch        {torch.__version__}  (CUDA: {torch.cuda.is_available()})')
print(f'  transformers {transformers.__version__}')
print(f'  accelerate   {accelerate.__version__}')
"

python -c "
from src.models import LLMProviderType, Mode, SimulationMode
from src.llm_provider import build_llm_provider
p = build_llm_provider(LLMProviderType.SIMULATED, 42, SimulationMode.IMPROVING)
print(f'  SimulatedProvider OK')
"

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  - Run a smoke test:     python main.py --episodes 3 --out test_smoke.json"
Write-Host "  - Run curriculum test:  python main.py --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --episodes 10 --out test_curriculum.json"
Write-Host "  - Run with real model:  python main.py --llm-provider real_local --llm-model Qwen/Qwen2.5-0.5B-Instruct --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --episodes 60 --out run_summary_real.json"
Write-Host ""
Write-Host "Models (auto-download, not in git):"
Write-Host "  - Qwen/Qwen2.5-0.5B-Instruct  (988 MB, from HuggingFace)"
if ($Cuda) {
    Write-Host "  - torch with CUDA 12.4 enabled"
}
