from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CapabilityToken:
    name: str
    trust_tier_required: int


class PolicyGate:
    """Simple capability + trust-tier policy gate."""

    def __init__(self, allowed_sources: set[str] | None = None) -> None:
        self.allowed_sources = allowed_sources or {"telegram", "slack", "discord", "local"}

    def validate_source(self, source: str) -> None:
        if source not in self.allowed_sources:
            raise PermissionError(f"Unsupported source: {source}")

    def enforce_capability(self, trust_tier: int, capability: CapabilityToken) -> None:
        if trust_tier < capability.trust_tier_required:
            raise PermissionError(
                f"Capability {capability.name} requires tier {capability.trust_tier_required}, got {trust_tier}"
            )
