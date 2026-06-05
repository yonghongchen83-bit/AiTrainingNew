# AITraining2

Minimal runnable closed loop for the meta-cognitive training architecture defined in Docs/AiDevelopmenPlan.txt.

This runtime includes an official swappable LLM provider layer so framework verification can run with a simulated backend or a real-provider stub.

## Run

```bash
python main.py --episodes 120
```

Run with explicit simulated provider:

```bash
python main.py --episodes 120 --llm-provider simulated --out run_summary_simulated.json
```

Run with real-provider stub wiring (no external API calls):

```bash
python main.py --episodes 40 --llm-provider real_stub --llm-model gpt-5.3-codex --out run_summary_real_stub.json
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

- Implements Phase 0-4 runnable loop.
- Uses canonical toolbox tools with multi-trigger alias words.
- Includes official swappable LLM provider abstraction (simulated + real_stub).
