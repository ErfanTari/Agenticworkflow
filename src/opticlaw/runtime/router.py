from __future__ import annotations

from collections import OrderedDict

from opticlaw.core.policy import PolicyGate
from opticlaw.core.types import EventEnvelope


class EventRouter:
    """Validates source and performs dedupe by event_id with bounded memory."""

    def __init__(self, policy_gate: PolicyGate, dedupe_cache_size: int = 10_000) -> None:
        self._policy_gate = policy_gate
        self._seen_events: OrderedDict[str, None] = OrderedDict()
        self._dedupe_cache_size = dedupe_cache_size

    async def accept(self, event: EventEnvelope) -> bool:
        self._policy_gate.validate_source(event.source)
        if event.event_id in self._seen_events:
            return False

        self._seen_events[event.event_id] = None
        self._seen_events.move_to_end(event.event_id)
        if len(self._seen_events) > self._dedupe_cache_size:
            self._seen_events.popitem(last=False)
        return True
