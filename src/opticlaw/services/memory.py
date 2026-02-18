from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from opticlaw.core.types import MemoryRecord, MemoryType


@dataclass(slots=True)
class RetrievalSlice:
    episodic: list[MemoryRecord]
    semantic: list[MemoryRecord]
    procedural: list[MemoryRecord]


class MemoryService:
    """Hierarchical memory with lightweight local storage in-memory for prototype."""

    def __init__(self, max_episodic: int = 500) -> None:
        self._episodic: deque[MemoryRecord] = deque(maxlen=max_episodic)
        self._semantic: list[MemoryRecord] = []
        self._procedural: list[MemoryRecord] = []

    async def store(self, record: MemoryRecord) -> None:
        if record.memory_type is MemoryType.EPISODIC:
            self._episodic.append(record)
        elif record.memory_type is MemoryType.SEMANTIC:
            self._semantic.append(record)
        else:
            self._procedural.append(record)

    async def retrieve(self, query: str, limit: int = 5) -> RetrievalSlice:
        query_lc = query.lower()
        episodic = [r for r in reversed(self._episodic) if query_lc in r.content.lower()][:limit]
        semantic = [r for r in self._semantic if query_lc in r.content.lower()][:limit]
        procedural = [r for r in self._procedural if query_lc in r.content.lower()][:limit]
        return RetrievalSlice(episodic=episodic, semantic=semantic, procedural=procedural)

    async def compact(self, salience_threshold: float = 0.15) -> None:
        self._semantic = [r for r in self._semantic if r.salience >= salience_threshold]
        self._procedural = [r for r in self._procedural if r.salience >= salience_threshold]
