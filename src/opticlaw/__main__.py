from __future__ import annotations

import asyncio

from opticlaw.core.types import EventEnvelope
from opticlaw.runtime.app import OptiClawApp


async def main() -> None:
    app = OptiClawApp()
    await app.ingest(EventEnvelope(source="local", user_id="u1", thread_id="t1", text="/status"))
    await app.ingest(
        EventEnvelope(
            source="local",
            user_id="u1",
            thread_id="t1",
            text="Please run echo 'hello from opticlaw'",
        )
    )
    await app.run_until_idle()
    for line in app.responses:
        print(line)


if __name__ == "__main__":
    asyncio.run(main())
