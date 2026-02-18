from __future__ import annotations

from uuid import uuid4

from opticlaw.core.types import EventEnvelope, TaskGraph, TaskNode
from opticlaw.services.llm import LLMClient
from opticlaw.services.model_router import ModelRouter, ModelSelection


class PlannerEngine:
    """Transforms goals into task graphs and model selections."""

    def __init__(self, model_router: ModelRouter, llm_client: LLMClient) -> None:
        self._router = model_router
        self._llm = llm_client

    async def build_plan(self, event: EventEnvelope, budget_cost: float = 0.05) -> tuple[TaskGraph, ModelSelection]:
        complexity = min(1.0, max(0.1, len(event.text.split()) / 20))
        model = self._router.select(complexity=complexity, requires_privacy=True, budget_cost=budget_cost)
        draft = await self._llm.decompose_goal(event.text)

        nodes: list[TaskNode] = []
        previous_node_id: str | None = None
        seen_tool_instructions: set[str] = set()
        for idx, step in enumerate(draft.steps[:6]):
            node_id = f"step_{idx + 1}"
            lower = step.lower()
            kind = "reason"
            instruction = step

            if "execute command:" in lower or "run " in lower:
                kind = "tool"
                instruction = self._extract_command(step, event.text)
            elif "email" in lower:
                kind = "tool"
                instruction = self._extract_email_instruction(event.text)
            elif "summarize" in lower or "respond" in lower:
                kind = "message"

            if kind == "tool" and instruction in seen_tool_instructions:
                continue

            deps = (previous_node_id,) if previous_node_id else ()
            nodes.append(TaskNode(node_id=node_id, kind=kind, instruction=instruction, deps=deps))
            previous_node_id = node_id
            if kind == "tool":
                seen_tool_instructions.add(instruction)

        if not any(node.kind == "message" for node in nodes):
            deps = (previous_node_id,) if previous_node_id else ()
            nodes.append(TaskNode(node_id="respond", kind="message", instruction="Summarize outcome for user", deps=deps))

        graph = TaskGraph(task_id=str(uuid4()), goal=event.text, nodes=nodes)
        return graph, model

    @staticmethod
    def _extract_command(step: str, goal: str) -> str:
        lower_step = step.lower()
        if "execute command:" in lower_step:
            _, command = step.split(":", 1)
            return command.strip() or "echo 'No command specified'"
        if "run " in goal.lower():
            return goal.lower().split("run ", 1)[1].strip() or "echo 'No command specified'"
        return "echo 'No command specified'"

    @staticmethod
    def _extract_email_instruction(goal: str) -> str:
        # Expected format for real delivery: to=<email>;subject=<subject>;body=<content>
        if "to=" in goal and "subject=" in goal and "body=" in goal:
            return goal
        return "to=draft@example.com;subject=Draft;body=Generated draft email action"
