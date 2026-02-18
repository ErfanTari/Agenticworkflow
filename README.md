# OptiClaw Prototype

A clean, sustainable, and efficient **event-driven** prototype based on `OPTICLAW_BLUEPRINT.md`.

## Features
- No heartbeat scheduler (event-driven queue + one-shot deferred tasks).
- Event router with source validation and bounded dedupe cache.
- Cheap triage path before planning.
- Planner + model router + LLM decomposition abstraction.
- Real shell execution connector (with timeout and safety blocklist).
- Email connector with dry-run mode + optional SMTP send.
- Hierarchical memory service with SQLite persistence.
- Async-first runtime with error-resilient event handling.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
PYTHONPATH=src python -m opticlaw
```

## Run tests
```bash
pytest -q
```

## Optional integrations
- **Ollama planning decomposition**
  - `export OPTICLAW_OLLAMA_URL=http://localhost:11434`
  - `export OPTICLAW_OLLAMA_MODEL=qwen2.5:3b`
- **SMTP email sending** (otherwise dry-run)
  - `export OPTICLAW_SMTP_HOST=smtp.gmail.com`
  - `export OPTICLAW_SMTP_PORT=587`
  - `export OPTICLAW_SMTP_USER=you@example.com`
  - `export OPTICLAW_SMTP_PASS=app-password`
  - `export OPTICLAW_SMTP_FROM=you@example.com`
