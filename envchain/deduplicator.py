"""Deduplicator: detect and remove duplicate environment variable values within a chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain.chain import EnvChain, EnvVar


@dataclass
class DedupeResult:
    profile: str
    duplicates: Dict[str, List[str]]  # value -> list of keys sharing it
    kept: List[str]  # keys retained in the output chain
    dropped: List[str]  # keys removed as duplicates
    chain: EnvChain

    def __repr__(self) -> str:
        return (
            f"DedupeResult(profile={self.profile!r}, "
            f"duplicate_groups={len(self.duplicates)}, "
            f"kept={len(self.kept)}, dropped={len(self.dropped)})"
        )

    @property
    def is_clean(self) -> bool:
        """True when no duplicates were found."""
        return len(self.dropped) == 0


def deduplicate_chain(
    chain: EnvChain,
    *,
    keep: str = "first",
) -> DedupeResult:
    """Return a new chain with duplicate values removed.

    Args:
        chain: The source :class:`EnvChain` to process.
        keep: Which occurrence to keep when a value appears more than once.
              ``"first"`` (default) retains the first key seen; ``"last"``
              retains the final key.

    Returns:
        A :class:`DedupeResult` describing what changed.
    """
    if keep not in {"first", "last"}:
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    # Group keys by their resolved value (None values are never considered dups)
    value_to_keys: Dict[str, List[str]] = {}
    for var in chain.vars:
        val = var.resolve()
        if val is None:
            continue
        value_to_keys.setdefault(val, []).append(var.key)

    duplicates = {v: keys for v, keys in value_to_keys.items() if len(keys) > 1}

    dropped_keys: set[str] = set()
    for keys in duplicates.values():
        losers = keys[1:] if keep == "first" else keys[:-1]
        dropped_keys.update(losers)

    kept_vars: List[EnvVar] = []
    kept_keys: List[str] = []
    dropped_keys_ordered: List[str] = []

    for var in chain.vars:
        if var.key in dropped_keys:
            dropped_keys_ordered.append(var.key)
        else:
            kept_vars.append(var)
            kept_keys.append(var.key)

    new_chain = EnvChain(profile=chain.profile)
    for var in kept_vars:
        new_chain.add(var)

    return DedupeResult(
        profile=chain.profile,
        duplicates=duplicates,
        kept=kept_keys,
        dropped=dropped_keys_ordered,
        chain=new_chain,
    )
