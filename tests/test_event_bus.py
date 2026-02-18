import asyncio

from opticlaw.core.types import EventEnvelope
from opticlaw.runtime.event_bus import EventBus


def test_schedule_once_dispatches_event() -> None:
    async def run() -> None:
        bus = EventBus()
        received: list[str] = []

        async def handler(event: EventEnvelope) -> None:
            received.append(event.text)
            bus.stop()

        runner = asyncio.create_task(bus.run(handler))
        await bus.schedule_once(0.01, EventEnvelope(source="local", user_id="u", thread_id="t", text="deferred"))
        await runner
        assert received == ["deferred"]

    asyncio.run(run())
