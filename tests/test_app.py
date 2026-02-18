import asyncio

from opticlaw.core.types import EventEnvelope
from opticlaw.runtime.app import OptiClawApp


def test_fast_path_response() -> None:
    async def run() -> None:
        app = OptiClawApp()
        await app.ingest(EventEnvelope(source="local", user_id="u", thread_id="t", text="/status"))
        await app.run_until_idle(0.05)
        assert len(app.responses) == 1
        assert "event-driven" in app.responses[0]

    asyncio.run(run())


def test_plan_and_execute_response() -> None:
    async def run() -> None:
        app = OptiClawApp()
        await app.ingest(
            EventEnvelope(source="local", user_id="u", thread_id="t", text="Please build and run this task")
        )
        await app.run_until_idle(0.05)
        assert len(app.responses) == 1
        assert "[local:" in app.responses[0]
        assert "shell-sandbox" in app.responses[0]

    asyncio.run(run())


def test_router_deduplicates_events() -> None:
    async def run() -> None:
        app = OptiClawApp()
        event = EventEnvelope(source="local", user_id="u", thread_id="t", text="ping", event_id="dup")
        await app.ingest(event)
        await app.ingest(event)
        await app.run_until_idle(0.05)
        assert len(app.responses) == 1

    asyncio.run(run())
