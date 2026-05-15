"""Clone an EnvChain from one profile to another, optionally transforming keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .chain import EnvChain, EnvVar
from .profiles import KNOWN_PROFILES


@dataclass
class CloneResult:
    source_profile: str
    target_profile: str
    cloned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CloneResult(source={self.source_profile!r}, "
            f"target={self.target_profile!r}, "
            f"cloned={len(self.cloned)}, skipped={len(self.skipped)})"
        )

    @property
    def is_empty(self) -> bool:
        return len(self.cloned) == 0


KeyTransform = Callable[[str], str]


def clone_chain(
    source: EnvChain,
    target_profile: str,
    *,
    key_transform: Optional[KeyTransform] = None,
    overwrite: bool = True,
    exclude: Optional[List[str]] = None,
) -> tuple[EnvChain, CloneResult]:
    """Clone *source* into a new EnvChain with *target_profile*.

    Args:
        source: The chain to clone from.
        target_profile: Profile name for the resulting chain.
        key_transform: Optional callable applied to each key before inserting.
        overwrite: When False, keys already resolved in target env are skipped.
        exclude: List of keys to exclude from the clone.

    Returns:
        A tuple of (new EnvChain, CloneResult).
    """
    if target_profile not in KNOWN_PROFILES:
        raise ValueError(
            f"Unknown target profile {target_profile!r}. "
            f"Expected one of {KNOWN_PROFILES}."
        )

    excluded = set(exclude or [])
    result = CloneResult(
        source_profile=source.profile,
        target_profile=target_profile,
    )

    cloned_chain = EnvChain(profile=target_profile)

    for var in source.vars:
        if var.key in excluded:
            result.skipped.append(var.key)
            continue

        new_key = key_transform(var.key) if key_transform else var.key

        if not overwrite and cloned_chain.get(new_key) is not None:
            result.skipped.append(var.key)
            continue

        cloned_chain.add(EnvVar(key=new_key, default=var.default))
        result.cloned.append(var.key)

    return cloned_chain, result
