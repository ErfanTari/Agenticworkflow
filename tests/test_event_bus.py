import asyncio

from opticlaw.core.policy import PolicyGate
from opticlaw.core.types import EventEnvelope
from opticlaw.runtime.event_bus import EventBus
from opticlaw.runtime.router import EventRouter


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


def test_router_dedupe_cache_is_bounded() -> None:
    async def run() -> None:
        router = EventRouter(PolicyGate(), dedupe_cache_size=3)
        for i in range(5):
            accepted = await router.accept(
                EventEnvelope(source="local", user_id="u", thread_id="t", text="msg", event_id=f"e{i}")
            )
            assert accepted

        assert len(router._seen_events) == 3

    asyncio.run(run())
