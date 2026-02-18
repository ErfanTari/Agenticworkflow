from __future__ import annotations

from opticlaw.connectors.base import Connector, ConnectorResult


class EmailConnector(Connector):
    name = "email"

    async def run(self, instruction: str) -> ConnectorResult:
        return ConnectorResult(True, f"[email-oauth] prepared action: {instruction}")
