# Workspace Agents

## milestone-governor

Purpose:
- Enforce implementation visibility and milestone-based git commits.

When to use:
- Any coding or architecture task in this repository.
- Any request that changes modules or execution flow.

Governance requirements:
- Keep checkbox progress updated in Docs/ImplementationProgress.md.
- Keep formal plan updated in Docs/ImplementationPlan.md.
- Log architecture decisions in Docs/ArchitectureDecisionLog.md.
- Log module interaction changes in Docs/ModuleInteractionSpec.md.
- Log execution commands and key outputs in Docs/ExecutionLog.md.
- Commit once per completed milestone with message prefix: milestone: <name>.

---

## stage-testing-agent

Purpose:
- Systematically verify the training framework captures metrics, detects model behavior, and finds the real model boundary.
- Encodes a reproducible flow: smart mode test → dumb mode test → real model test.

When to use:
- First time setting up this project on a new machine.
- After modifying the LLM provider layer or curriculum controller.
- Before pushing changes that affect metrics capture or boundary detection.

### Test package convention

Each test lives in `training/materials/<test_name>/` and is self-contained:

```
training/materials/<test_name>/
├── config/test_contract.json       ← parameters (gate, max loops, etc.)
├── runtime/controller.py            ← curriculum loop
├── simulation/simulator.py          ← fake LLM (exposes create_simulator())
├── output/                          ← run results
└── reward/reward.py                 ← custom reward (optional)
```

The `src/` folder is **test-agnostic** — no test-specific code lives outside `training/materials/`.

---

### Phase 1 — Smart mode (verify known boundary)

The DigitCounting simulator (`simulation/simulator.py`) has:
- ≤3 digits: 100% correct, conf=1.0
- 4 digits: 90% correct
- ≥5 digits: 60% correct

Run:
```powershell
python main.py --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_smart.json
```

Expected: `stop_reason: DigitCountingCapabilityBoundary@4Digits`, `max_verified_digits: 3`

---

### Phase 2 — Dumb mode (verify early termination)

Run:
```powershell
python main.py --dumb-mode --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_dumb.json
```

Expected: `stop_reason: DigitCountingCapabilityBoundary@1Digits`, `success_rate: 0.0`, fallback events populated.

---

### Phase 3 — Real model boundary

```powershell
python main.py --llm-provider real_local --llm-model Qwen/Qwen2.5-0.5B-Instruct --stage-test-root DigitCounting=training/materials/digit_counting_curriculum_v1 --mode Expert --episodes 60 --out training/materials/digit_counting_curriculum_v1/output/test_real.json
```

What to look for:
- `stop_reason`: capability boundary the real model hits
- `calibration_error`: how well it self-calibrates
- `false_high_confidence`: does it know when it doesn't know?

---

### Provider comparison

| Provider | CLI | GPU | Speed | Use |
|----------|-----|-----|-------|-----|
| `simulated` | `--llm-provider simulated` | N/A | Instant | Framework + test verification |
| `real_stub` | `--llm-provider real_stub` | N/A | Instant | Interface testing |
| `real_local` | `--llm-provider real_local --llm-model <hf-id>` | If CUDA | Slow CPU | Real model boundary |
| `real_vllm` | `--llm-provider real_vllm --llm-model <name> --llm-base-url <url>` | Via Ollama | Fast | Production |

---

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: torch` | Not installed | `pip install torch` |
| Model re-downloads every run | Cache issue | Check `~/.cache/huggingface/hub/` |
| CPU training too slow | CPU inference | Install CUDA torch or reduce `max_loops_per_level` in test_contract |
| Always `confidence=0.35` | Model can't output JSON | Format compliance is itself a boundary finding |
| Always `confidence=0.35` | Model output not JSON-parsable | Check raw model output; may need prompt tweaking |
| `real_vllm` timeouts | Ollama not running or wrong URL | `curl http://localhost:11434/api/tags` to verify |
