"""Inspect individual EnvVar entries with detailed metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class InspectEntry:
    """Detailed inspection result for a single environment variable."""

    key: str
    value: Optional[str]
    default: Optional[str]
    has_value: bool
    has_default: bool
    is_empty: bool
    source: str  # 'env', 'default', or 'missing'
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InspectEntry(key={self.key!r}, source={self.source!r}, "
            f"has_value={self.has_value}, is_empty={self.is_empty})"
        )


@dataclass
class InspectReport:
    """Collection of inspection entries for a chain."""

    profile: str
    entries: List[InspectEntry]

    def get(self, key: str) -> Optional[InspectEntry]:
        """Return the InspectEntry for *key*, or None if not found."""
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    @property
    def missing(self) -> List[InspectEntry]:
        """Entries where no value and no default are present."""
        return [e for e in self.entries if e.source == "missing"]

    @property
    def sourced_from_default(self) -> List[InspectEntry]:
        """Entries whose value comes from a default."""
        return [e for e in self.entries if e.source == "default"]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InspectReport(profile={self.profile!r}, "
            f"total={len(self.entries)}, missing={len(self.missing)})"
        )


def inspect_chain(chain: EnvChain) -> InspectReport:
    """Build an :class:`InspectReport` from *chain*."""
    entries: List[InspectEntry] = []
    for var in chain.vars:
        resolved = var.resolve()
        has_value = resolved is not None
        has_default = var.default is not None

        if resolved is not None and var.resolve() != var.default:
            source = "env"
        elif has_default and resolved == var.default:
            source = "default"
        elif has_default and not has_value:
            source = "default"
        elif has_value:
            source = "env"
        else:
            source = "missing"

        entries.append(
            InspectEntry(
                key=var.key,
                value=resolved,
                default=var.default,
                has_value=has_value,
                has_default=has_default,
                is_empty=resolved == "",
                source=source,
            )
        )
    return InspectReport(profile=chain.profile, entries=entries)
