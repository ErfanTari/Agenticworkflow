import asyncio
from pathlib import Path

from opticlaw.core.types import EventEnvelope, MemoryRecord, MemoryType
from opticlaw.runtime.app import OptiClawApp


def test_fast_path_response(tmp_path: Path) -> None:
    async def run() -> None:
        app = OptiClawApp(memory_db_path=str(tmp_path / "memory.db"))
        await app.ingest(EventEnvelope(source="local", user_id="u", thread_id="t", text="/status"))
        await app.run_until_idle(0.05)
        assert len(app.responses) == 1
        assert "event-driven" in app.responses[0]

    asyncio.run(run())


def test_plan_and_execute_response_runs_shell(tmp_path: Path) -> None:
    async def run() -> None:
        app = OptiClawApp(memory_db_path=str(tmp_path / "memory.db"))
        await app.ingest(
            EventEnvelope(source="local", user_id="u", thread_id="t", text="Please run echo integration_ok")
        )
        await app.run_until_idle(0.2)
        assert len(app.responses) == 1
        assert "[local:" in app.responses[0]
        assert "integration_ok" in app.responses[0]

    asyncio.run(run())


def test_router_deduplicates_events(tmp_path: Path) -> None:
    async def run() -> None:
        app = OptiClawApp(memory_db_path=str(tmp_path / "memory.db"))
        event = EventEnvelope(source="local", user_id="u", thread_id="t", text="ping", event_id="dup")
        await app.ingest(event)
        await app.ingest(event)
        await app.run_until_idle(0.05)
        assert len(app.responses) == 1

    asyncio.run(run())


def test_memory_persists_records(tmp_path: Path) -> None:
    async def run() -> None:
        db_path = tmp_path / "memory.db"
        app = OptiClawApp(memory_db_path=str(db_path))
        await app.memory.store(MemoryRecord(MemoryType.SEMANTIC, "project preference: tests first", salience=0.9))
        found = await app.memory.retrieve("tests first", limit=3)
        assert any("tests first" in rec.content for rec in found.semantic + found.episodic)

    asyncio.run(run())
