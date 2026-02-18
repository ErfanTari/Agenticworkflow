from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class Priority(str, Enum):
    USER_BLOCKING = "user_blocking"
    INTERACTIVE = "interactive"
    BACKGROUND = "background"
    MAINTENANCE = "maintenance"


class Decision(str, Enum):
    FAST_REPLY = "fast_reply"
    PLAN_AND_EXECUTE = "plan_and_execute"


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass(slots=True)
class EventEnvelope:
    source: str
    user_id: str
    thread_id: str
    text: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.INTERACTIVE


@dataclass(slots=True)
class ExecutionContext:
    request_id: str
    trust_tier: int = 0
    budget_ms: int = 25_000
    budget_cost: float = 0.05


@dataclass(slots=True)
class TaskNode:
    node_id: str
    kind: str
    instruction: str
    requires_approval: bool = False
    deps: tuple[str, ...] = ()


@dataclass(slots=True)
class TaskGraph:
    task_id: str
    goal: str
    nodes: list[TaskNode]


@dataclass(slots=True)
class MemoryRecord:
    memory_type: MemoryType
    content: str
    salience: float = 0.5
    entities: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
