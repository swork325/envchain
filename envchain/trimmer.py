"""Trim an EnvChain to only keys that satisfy a size or count constraint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class TrimResult:
    profile: str
    kept: list[EnvVar] = field(default_factory=list)
    dropped: list[EnvVar] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"TrimResult(profile={self.profile!r}, "
            f"kept={len(self.kept)}, dropped={len(self.dropped)})"
        )

    @property
    def is_clean(self) -> bool:
        """True when nothing was dropped."""
        return len(self.dropped) == 0

    def to_chain(self) -> EnvChain:
        """Return a new EnvChain containing only the kept variables."""
        chain = EnvChain(profile=self.profile)
        for var in self.kept:
            chain.add(var)
        return chain


def trim_chain(
    chain: EnvChain,
    *,
    max_keys: Optional[int] = None,
    max_value_length: Optional[int] = None,
    drop_empty: bool = False,
) -> TrimResult:
    """Return a TrimResult after applying the requested constraints.

    Parameters
    ----------
    chain:
        The source chain to trim.
    max_keys:
        When set, keep only the first *max_keys* variables (by insertion order).
    max_value_length:
        Drop any variable whose resolved value exceeds this character length.
    drop_empty:
        When True, drop variables whose resolved value is None or the empty string.
    """
    result = TrimResult(profile=chain.profile)

    for var in chain.vars:
        value = var.resolve()

        if drop_empty and (value is None or value == ""):
            result.dropped.append(var)
            continue

        if max_value_length is not None and value is not None and len(value) > max_value_length:
            result.dropped.append(var)
            continue

        if max_keys is not None and len(result.kept) >= max_keys:
            result.dropped.append(var)
            continue

        result.kept.append(var)

    return result
