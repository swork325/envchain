"""Patch an existing EnvChain by applying a dict of overrides or removals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class PatchResult:
    """Summary of changes applied by a patch operation."""

    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PatchResult(added={self.added}, "
            f"updated={self.updated}, removed={self.removed})"
        )

    @property
    def is_empty(self) -> bool:
        """Return True when the patch produced no changes."""
        return not (self.added or self.updated or self.removed)


def patch_chain(
    chain: EnvChain,
    overrides: Optional[Dict[str, Optional[str]]] = None,
    removals: Optional[List[str]] = None,
) -> tuple[EnvChain, PatchResult]:
    """Return a new EnvChain with *overrides* applied and *removals* dropped.

    Parameters
    ----------
    chain:
        The source chain to patch.
    overrides:
        Mapping of key -> new value.  A value of ``None`` sets the variable
        back to having no resolved value (only its default, if any).
    removals:
        Keys to remove entirely from the resulting chain.

    Returns
    -------
    tuple[EnvChain, PatchResult]
        The patched chain and a summary of what changed.
    """
    overrides = overrides or {}
    removals = set(removals or [])

    result = PatchResult()
    existing_keys = {var.key: var for var in chain._vars}  # type: ignore[attr-defined]

    new_vars: List[EnvVar] = []
    for var in chain._vars:  # type: ignore[attr-defined]
        if var.key in removals:
            result.removed.append(var.key)
            continue
        if var.key in overrides:
            new_val = overrides[var.key]
            new_vars.append(EnvVar(key=var.key, default=var.default, value=new_val))
            result.updated.append(var.key)
        else:
            new_vars.append(var)

    for key, value in overrides.items():
        if key not in existing_keys and key not in removals:
            new_vars.append(EnvVar(key=key, value=value))
            result.added.append(key)

    patched = EnvChain(profile=chain.profile)
    for var in new_vars:
        patched.add(var)
    return patched, result
