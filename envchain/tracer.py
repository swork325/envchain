"""Trace the resolution path of environment variables across profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .chain import EnvChain


@dataclass
class TraceStep:
    profile: str
    key: str
    value: Optional[str]
    source: str  # 'env', 'default', 'missing'

    def __repr__(self) -> str:
        return f"TraceStep(profile={self.profile!r}, key={self.key!r}, source={self.source!r}, value={self.value!r})"


@dataclass
class TraceReport:
    key: str
    steps: List[TraceStep] = field(default_factory=list)

    def resolved_in(self) -> List[str]:
        """Return profiles where the key had a real (non-missing) value."""
        return [s.profile for s in self.steps if s.source != "missing"]

    def first_resolved(self) -> Optional[TraceStep]:
        """Return the first step where the key was resolved."""
        for step in self.steps:
            if step.source != "missing":
                return step
        return None

    def __repr__(self) -> str:
        resolved = self.first_resolved()
        summary = f"first={resolved.profile!r}" if resolved else "unresolved"
        return f"TraceReport(key={self.key!r}, {summary}, steps={len(self.steps)})"


def trace_key(key: str, chains: List[EnvChain]) -> TraceReport:
    """Trace how a single key resolves across a list of EnvChain instances."""
    if not chains:
        raise ValueError("chains must not be empty")

    report = TraceReport(key=key)
    for chain in chains:
        var = chain.get(key)
        if var is None:
            step = TraceStep(
                profile=chain.profile,
                key=key,
                value=None,
                source="missing",
            )
        else:
            value = var.resolve()
            if value is None:
                source = "missing"
            elif var.default is not None and value == var.default:
                source = "default"
            else:
                source = "env"
            step = TraceStep(
                profile=chain.profile,
                key=key,
                value=value,
                source=source,
            )
        report.steps.append(step)
    return report


def trace_all(chains: List[EnvChain]) -> List[TraceReport]:
    """Trace all keys found across all chains."""
    if not chains:
        raise ValueError("chains must not be empty")
    all_keys: list[str] = []
    seen: set[str] = set()
    for chain in chains:
        for key in chain.keys():
            if key not in seen:
                all_keys.append(key)
                seen.add(key)
    return [trace_key(k, chains) for k in all_keys]
