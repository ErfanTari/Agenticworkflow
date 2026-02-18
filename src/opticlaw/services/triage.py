from __future__ import annotations

from dataclasses import dataclass

from opticlaw.core.types import Decision, EventEnvelope


@dataclass(slots=True)
class TriageResult:
    decision: Decision
    confidence: float
    reason: str


class TriageEngine:
    """Cheap path triage using deterministic rules."""

    SIMPLE_PATTERNS = {"help", "status", "ping", "hello"}

    async def classify(self, event: EventEnvelope) -> TriageResult:
        text = event.text.strip().lower()
        if text in self.SIMPLE_PATTERNS or text.startswith("/"):
            return TriageResult(Decision.FAST_REPLY, 0.98, "rule_match")
        if any(word in text for word in ("build", "refactor", "email", "calendar", "run")):
            return TriageResult(Decision.PLAN_AND_EXECUTE, 0.86, "tooling_likely")
        if len(text.split()) < 8:
            return TriageResult(Decision.FAST_REPLY, 0.8, "short_message")
        return TriageResult(Decision.PLAN_AND_EXECUTE, 0.62, "default_complex")
