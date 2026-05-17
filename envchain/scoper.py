"""Scope filtering: restrict an EnvChain to a named scope (prefix group)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class ScopeResult:
    profile: str
    scope: str
    included: List[EnvVar] = field(default_factory=list)
    excluded: List[EnvVar] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ScopeResult(profile={self.profile!r}, scope={self.scope!r}, "
            f"included={len(self.included)}, excluded={len(self.excluded)})"
        )

    @property
    def is_empty(self) -> bool:
        return len(self.included) == 0


def scope_chain(
    chain: EnvChain,
    scope: str,
    *,
    separator: str = "_",
    strip_prefix: bool = False,
) -> tuple[EnvChain, ScopeResult]:
    """Return a new chain containing only vars whose key starts with *scope*.

    Parameters
    ----------
    chain:        Source chain.
    scope:        Prefix to match (case-insensitive, e.g. ``"DB"``).
    separator:    Character expected after the prefix (default ``"_"``).
    strip_prefix: When *True* the prefix + separator are removed from the
                  resulting keys.
    """
    prefix = scope.upper().rstrip(separator) + separator
    included: List[EnvVar] = []
    excluded: List[EnvVar] = []

    for var in chain._vars.values():
        if var.key.upper().startswith(prefix):
            if strip_prefix:
                new_key = var.key[len(prefix):]
                included.append(EnvVar(key=new_key, default=var.default))
            else:
                included.append(var)
        else:
            excluded.append(var)

    scoped = EnvChain(profile=chain.profile)
    for var in included:
        scoped.add(var)

    result = ScopeResult(
        profile=chain.profile,
        scope=scope,
        included=included,
        excluded=excluded,
    )
    return scoped, result
