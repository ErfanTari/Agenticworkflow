from __future__ import annotations

from opticlaw.connectors.base import Connector, ConnectorResult


class ShellConnector(Connector):
    name = "shell"

    async def run(self, instruction: str) -> ConnectorResult:
        return ConnectorResult(True, f"[shell-sandbox] executed: {instruction}")
