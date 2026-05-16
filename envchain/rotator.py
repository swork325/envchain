"""Rotate environment variable values across an EnvChain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class RotationResult:
    """Result of a rotation operation."""

    profile: str
    rotated: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"RotationResult(profile={self.profile!r}, "
            f"rotated={len(self.rotated)}, skipped={len(self.skipped)})"
        )

    @property
    def is_empty(self) -> bool:
        """Return True when no keys were rotated."""
        return len(self.rotated) == 0


def rotate_chain(
    chain: EnvChain,
    generator: Callable[[str, Optional[str]], Optional[str]],
    keys: Optional[List[str]] = None,
) -> tuple[EnvChain, RotationResult]:
    """Apply *generator* to each key in *chain* to produce new values.

    Parameters
    ----------
    chain:
        The source :class:`~envchain.chain.EnvChain`.
    generator:
        Callable that receives ``(key, current_value)`` and returns the new
        value, or ``None`` to skip rotation for that key.
    keys:
        Optional allowlist of keys to rotate.  When *None* all keys are
        considered.

    Returns
    -------
    tuple[EnvChain, RotationResult]
        A new chain with updated values and a :class:`RotationResult`
        describing what changed.
    """
    result = RotationResult(profile=chain.profile)
    new_chain = EnvChain(profile=chain.profile)

    for var in chain.vars:
        if keys is not None and var.key not in keys:
            new_chain.add(var)
            result.skipped.append(var.key)
            continue

        new_value = generator(var.key, var.value)
        if new_value is None:
            new_chain.add(var)
            result.skipped.append(var.key)
        else:
            new_chain.add(EnvVar(key=var.key, value=new_value, default=var.default))
            result.rotated[var.key] = new_value

    return new_chain, result
