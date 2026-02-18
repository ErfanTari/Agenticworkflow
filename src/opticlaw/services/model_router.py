from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModelSelection:
    provider: str
    model: str
    max_tokens: int
    temperature: float


class ModelRouter:
    """Budget-aware model routing policy."""

    def select(self, complexity: float, requires_privacy: bool, budget_cost: float) -> ModelSelection:
        if requires_privacy and complexity <= 0.4:
            return ModelSelection("local", "tiny", 256, 0.1)
        if complexity <= 0.6:
            return ModelSelection("local", "medium", 512, 0.2)
        if budget_cost >= 0.03:
            return ModelSelection("cloud", "frontier", 1024, 0.2)
        return ModelSelection("local", "medium", 768, 0.15)
