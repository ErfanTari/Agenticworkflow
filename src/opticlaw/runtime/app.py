from __future__ import annotations

import asyncio
from uuid import uuid4

from opticlaw.connectors.email import EmailConnector
from opticlaw.connectors.shell import ShellConnector
from opticlaw.core.policy import PolicyGate
from opticlaw.core.types import Decision, EventEnvelope, ExecutionContext, MemoryRecord, MemoryType
from opticlaw.runtime.event_bus import EventBus
from opticlaw.runtime.router import EventRouter
from opticlaw.services.memory import MemoryService
from opticlaw.services.model_router import ModelRouter
from opticlaw.services.orchestrator import ToolOrchestrator
from opticlaw.services.planner import PlannerEngine
from opticlaw.services.triage import TriageEngine


class OptiClawApp:
    """Composable app runtime implementing the prototype architecture."""

    def __init__(self) -> None:
        policy_gate = PolicyGate()
        self.event_bus = EventBus()
        self.router = EventRouter(policy_gate)
        self.triage = TriageEngine()
        self.memory = MemoryService()
        self.planner = PlannerEngine(ModelRouter())
        self.orchestrator = ToolOrchestrator(
            policy_gate=policy_gate,
            connectors={"shell": ShellConnector(), "email": EmailConnector()},
        )
        self.responses: list[str] = []

    async def ingest(self, event: EventEnvelope) -> None:
        await self.event_bus.publish(event)

    async def handle_event(self, event: EventEnvelope) -> None:
        accepted = await self.router.accept(event)
        if not accepted:
            return

        await self.memory.store(MemoryRecord(MemoryType.EPISODIC, f"in:{event.text}", salience=0.7))
        triage_result = await self.triage.classify(event)

        if triage_result.decision is Decision.FAST_REPLY:
            reply = self._fast_reply(event.text)
            self.responses.append(reply)
            await self.memory.store(MemoryRecord(MemoryType.EPISODIC, f"out:{reply}", salience=0.5))
            return

        context = ExecutionContext(request_id=str(uuid4()), trust_tier=1)
        graph, model = await self.planner.build_plan(event)
        outputs = await self.orchestrator.execute(graph, context)
        reply = f"[{model.provider}:{model.model}] " + " | ".join(outputs)
        self.responses.append(reply)

        await self.memory.store(MemoryRecord(MemoryType.PROCEDURAL, f"plan:{graph.goal}", salience=0.4))
        await self.memory.store(MemoryRecord(MemoryType.EPISODIC, f"out:{reply}", salience=0.6))

    async def run_until_idle(self, timeout_s: float = 0.2) -> None:
        task = asyncio.create_task(self.event_bus.run(self.handle_event))
        await asyncio.sleep(timeout_s)
        self.event_bus.stop()
        await task

    @staticmethod
    def _fast_reply(text: str) -> str:
        t = text.strip().lower()
        if t in {"help", "/help"}:
            return "OptiClaw: say what you need, I can plan and execute tasks efficiently."
        if t in {"status", "/status", "ping"}:
            return "OptiClaw is event-driven, awake on demand, and currently healthy."
        return f"Got it: {text}"
