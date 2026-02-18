from __future__ import annotations

import asyncio
import sqlite3
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

from opticlaw.core.types import MemoryRecord, MemoryType


@dataclass(slots=True)
class RetrievalSlice:
    episodic: list[MemoryRecord]
    semantic: list[MemoryRecord]
    procedural: list[MemoryRecord]


class MemoryService:
    """Hierarchical memory with in-memory cache + SQLite persistence."""

    def __init__(self, max_episodic: int = 500, db_path: str = "opticlaw_memory.db") -> None:
        self._episodic: deque[MemoryRecord] = deque(maxlen=max_episodic)
        self._semantic: list[MemoryRecord] = []
        self._procedural: list[MemoryRecord] = []
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    salience REAL NOT NULL,
                    entities TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    async def store(self, record: MemoryRecord) -> None:
        if record.memory_type is MemoryType.EPISODIC:
            self._episodic.append(record)
        elif record.memory_type is MemoryType.SEMANTIC:
            self._semantic.append(record)
        else:
            self._procedural.append(record)

        await asyncio.to_thread(self._persist_record, record)

    def _persist_record(self, record: MemoryRecord) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO memory_records(memory_type, content, salience, entities, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.memory_type.value,
                    record.content,
                    record.salience,
                    ",".join(record.entities),
                    record.created_at.isoformat(),
                ),
            )

    async def retrieve(self, query: str, limit: int = 5) -> RetrievalSlice:
        query_lc = query.lower()
        episodic = [r for r in reversed(self._episodic) if query_lc in r.content.lower()][:limit]
        semantic = [r for r in self._semantic if query_lc in r.content.lower()][:limit]
        procedural = [r for r in self._procedural if query_lc in r.content.lower()][:limit]

        if len(episodic) < limit:
            db_records = await asyncio.to_thread(self._retrieve_persisted, query_lc, limit)
            episodic.extend(db_records[: max(0, limit - len(episodic))])

        return RetrievalSlice(episodic=episodic, semantic=semantic, procedural=procedural)

    def _retrieve_persisted(self, query_lc: str, limit: int) -> list[MemoryRecord]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT memory_type, content, salience, entities, created_at
                FROM memory_records
                WHERE lower(content) LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{query_lc}%", limit),
            ).fetchall()

        records: list[MemoryRecord] = []
        for memory_type, content, salience, entities, created_at in rows:
            records.append(
                MemoryRecord(
                    memory_type=MemoryType(memory_type),
                    content=content,
                    salience=float(salience),
                    entities=tuple(filter(None, str(entities).split(","))),
                    created_at=datetime.fromisoformat(created_at).astimezone(timezone.utc),
                )
            )
        return records

    async def compact(self, salience_threshold: float = 0.15) -> None:
        self._semantic = [r for r in self._semantic if r.salience >= salience_threshold]
        self._procedural = [r for r in self._procedural if r.salience >= salience_threshold]
        await asyncio.to_thread(self._compact_persisted, salience_threshold)

    def _compact_persisted(self, salience_threshold: float) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM memory_records WHERE salience < ?", (salience_threshold,))
