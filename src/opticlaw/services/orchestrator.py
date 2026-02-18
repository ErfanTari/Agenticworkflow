from __future__ import annotations

from opticlaw.connectors.base import Connector
from opticlaw.core.policy import CapabilityToken, PolicyGate
from opticlaw.core.types import ExecutionContext, TaskGraph


class ToolOrchestrator:
    """Executes task graph nodes in dependency order with capability checks."""

    def __init__(self, policy_gate: PolicyGate, connectors: dict[str, Connector]) -> None:
        self._policy_gate = policy_gate
        self._connectors = connectors

    async def execute(self, graph: TaskGraph, context: ExecutionContext) -> list[str]:
        outputs: list[str] = []
        completed: set[str] = set()

        for node in graph.nodes:
            if any(dep not in completed for dep in node.deps):
                raise RuntimeError(f"Node dependency unresolved for {node.node_id}")

            if node.kind == "tool":
                capability = CapabilityToken("tool.execute", trust_tier_required=1)
                self._policy_gate.enforce_capability(context.trust_tier, capability)
                connector_key = self._pick_connector(graph.goal, node.instruction)
                connector = self._connectors[connector_key]
                result = await connector.run(node.instruction)
                if not result.success:
                    outputs.append(result.detail)
                    break
                outputs.append(result.detail)
            else:
                outputs.append(f"[{node.kind}] {node.instruction}")

            completed.add(node.node_id)

        return outputs

    @staticmethod
    def _pick_connector(goal: str, instruction: str) -> str:
        lowered = f"{goal} {instruction}".lower()
        if "email" in lowered or "to=" in lowered:
            return "email"
        return "shell"
