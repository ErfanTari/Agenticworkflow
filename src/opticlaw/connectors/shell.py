from __future__ import annotations

import asyncio
from opticlaw.connectors.base import Connector, ConnectorResult


class ShellConnector(Connector):
    name = "shell"

    async def run(self, instruction: str) -> ConnectorResult:
        command = instruction.strip()
        if not command:
            return ConnectorResult(False, "[shell-sandbox] empty command")

        # Minimal command hygiene for prototype safety.
        blocked = {"rm -rf /", "shutdown", "reboot", ":(){"}
        if any(token in command for token in blocked):
            return ConnectorResult(False, "[shell-sandbox] blocked dangerous command")

        process = await asyncio.create_subprocess_exec(
            "bash",
            "-lc",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=8)
        except TimeoutError:
            process.kill()
            return ConnectorResult(False, "[shell-sandbox] command timed out")

        out_text = stdout.decode().strip()
        err_text = stderr.decode().strip()
        if process.returncode != 0:
            detail = err_text or out_text or f"exit={process.returncode}"
            return ConnectorResult(False, f"[shell-sandbox] failed: {detail}")

        detail = out_text if out_text else "ok"
        return ConnectorResult(True, f"[shell-sandbox] {detail}")
