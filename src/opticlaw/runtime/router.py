from __future__ import annotations

from opticlaw.core.policy import PolicyGate
from opticlaw.core.types import EventEnvelope


class EventRouter:
    """Validates source and performs dedupe by event_id."""

    def __init__(self, policy_gate: PolicyGate) -> None:
        self._policy_gate = policy_gate
        self._seen_events: set[str] = set()

    async def accept(self, event: EventEnvelope) -> bool:
        self._policy_gate.validate_source(event.source)
        if event.event_id in self._seen_events:
            return False
        self._seen_events.add(event.event_id)
        return True
