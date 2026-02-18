# OptiClaw Prototype

A clean, sustainable, and efficient **event-driven** prototype based on `OPTICLAW_BLUEPRINT.md`.

## Features
- No heartbeat scheduler.
- Event router with idempotency.
- Cheap triage path before planning.
- Planner + model router + orchestrator.
- Hierarchical memory service with salience-aware compression hooks.
- Capability-gated tool connector stubs.
- Async-first runtime with deferred one-shot scheduling.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
python -m opticlaw
```

## Run tests
```bash
pytest -q
```
