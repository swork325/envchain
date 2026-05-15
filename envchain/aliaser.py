"""Aliaser: map environment variable keys to human-friendly aliases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class AliasedVar:
    """An EnvVar paired with its alias (if any)."""

    var: EnvVar
    alias: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        alias_part = f", alias={self.alias!r}" if self.alias else ""
        return f"AliasedVar(key={self.var.key!r}{alias_part})"

    @property
    def display_key(self) -> str:
        """Return alias if set, otherwise the original key."""
        return self.alias if self.alias else self.var.key


@dataclass
class AliasReport:
    """Report of all aliased variables for a chain."""

    profile: str
    entries: List[AliasedVar] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"AliasReport(profile={self.profile!r}, total={len(self.entries)})"

    @property
    def aliased_keys(self) -> List[str]:
        """Return original keys that have an alias assigned."""
        return [e.var.key for e in self.entries if e.alias is not None]

    def by_alias(self, alias: str) -> Optional[AliasedVar]:
        """Look up an entry by alias."""
        for entry in self.entries:
            if entry.alias == alias:
                return entry
        return None


def alias_chain(
    chain: EnvChain,
    alias_map: Dict[str, str],
) -> AliasReport:
    """Attach aliases to variables in *chain* according to *alias_map*.

    Args:
        chain: The EnvChain whose variables should be aliased.
        alias_map: Mapping of ``{original_key: alias}``.

    Returns:
        An :class:`AliasReport` containing one :class:`AliasedVar` per variable.
    """
    entries: List[AliasedVar] = []
    for var in chain.vars:
        alias = alias_map.get(var.key)
        entries.append(AliasedVar(var=var, alias=alias))
    return AliasReport(profile=chain.profile, entries=entries)
