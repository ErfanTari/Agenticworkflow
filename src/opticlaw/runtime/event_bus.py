from __future__ import annotations

import asyncio
import heapq
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from opticlaw.core.types import EventEnvelope, Priority

Handler = Callable[[EventEnvelope], Awaitable[None]]


@dataclass(order=True)
class QueueItem:
    rank: int
    seq: int
    event: EventEnvelope = field(compare=False)


PRIORITY_RANK = {
    Priority.USER_BLOCKING: 0,
    Priority.INTERACTIVE: 1,
    Priority.BACKGROUND: 2,
    Priority.MAINTENANCE: 3,
}


class EventBus:
    """Pure event-driven queue with one-shot deferred scheduling."""

    def __init__(self) -> None:
        self._queue: list[QueueItem] = []
        self._seq = 0
        self._new_event = asyncio.Event()
        self._stopping = False

    async def publish(self, event: EventEnvelope) -> None:
        heapq.heappush(self._queue, QueueItem(PRIORITY_RANK[event.priority], self._seq, event))
        self._seq += 1
        self._new_event.set()

    async def schedule_once(self, delay_s: float, event: EventEnvelope) -> None:
        loop = asyncio.get_running_loop()

        def _enqueue() -> None:
            loop.create_task(self.publish(event))

        loop.call_later(delay_s, _enqueue)

    async def run(self, handler: Handler) -> None:
        while not self._stopping:
            if not self._queue:
                self._new_event.clear()
                await self._new_event.wait()
                continue

            item = heapq.heappop(self._queue)
            await handler(item.event)

    def stop(self) -> None:
        self._stopping = True
        self._new_event.set()
