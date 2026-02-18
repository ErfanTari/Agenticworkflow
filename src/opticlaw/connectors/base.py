from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConnectorResult:
    success: bool
    detail: str


class Connector:
    name = "base"

    async def run(self, instruction: str) -> ConnectorResult:
        raise NotImplementedError
