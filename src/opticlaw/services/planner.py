from __future__ import annotations

from uuid import uuid4

from opticlaw.core.types import EventEnvelope, TaskGraph, TaskNode
from opticlaw.services.model_router import ModelRouter, ModelSelection


class PlannerEngine:
    """Transforms goals into task graphs and model selections."""

    def __init__(self, model_router: ModelRouter) -> None:
        self._router = model_router

    async def build_plan(self, event: EventEnvelope, budget_cost: float = 0.05) -> tuple[TaskGraph, ModelSelection]:
        complexity = min(1.0, max(0.1, len(event.text.split()) / 20))
        model = self._router.select(complexity=complexity, requires_privacy=True, budget_cost=budget_cost)
        nodes = [
            TaskNode("analyze", "reason", f"Analyze request: {event.text}"),
            TaskNode("act", "tool", "Run selected connector or local action", deps=("analyze",)),
            TaskNode("respond", "message", "Synthesize concise response", deps=("act",)),
        ]
        graph = TaskGraph(task_id=str(uuid4()), goal=event.text, nodes=nodes)
        return graph, model
