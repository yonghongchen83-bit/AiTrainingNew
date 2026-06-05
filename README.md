# AITraining2

Minimal runnable closed loop for the meta-cognitive training architecture defined in Docs/AiDevelopmenPlan.txt.

## Run

```bash
python main.py --episodes 120
```

Run full Stage 0-4 loop with self-extension enabled:

```bash
python main.py --episodes 120 --enable-self-extension --self-task-count 60 --out run_summary_phase4.json
```

## Milestone Bootstrap

Use the helper to pre-seed governance docs for a new milestone:

```bash
python scripts/start_milestone.py --name "your milestone" --apply
```

## Scope

- Implements Phase 0-2 runnable loop.
- Uses Chinese native trigger words for toolbox tools.
- Includes Stage 3-4 self-extension stubs only (no implementation/testing).
