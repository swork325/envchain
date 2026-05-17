"""Split an EnvChain into multiple sub-chains based on a predicate or key list."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class SplitResult:
    """Result of splitting a chain into two parts: matched and remainder."""

    profile: str
    matched: EnvChain
    remainder: EnvChain

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SplitResult(profile={self.profile!r}, "
            f"matched={len(self.matched.vars)}, "
            f"remainder={len(self.remainder.vars)})"
        )

    def is_empty(self) -> bool:
        """Return True when no variables matched the split predicate."""
        return len(self.matched.vars) == 0


def split_chain(
    chain: EnvChain,
    *,
    keys: Optional[List[str]] = None,
    predicate: Optional[Callable[[EnvVar], bool]] = None,
) -> SplitResult:
    """Split *chain* into matched / remainder sub-chains.

    Exactly one of *keys* or *predicate* must be supplied.

    Parameters
    ----------
    chain:      Source chain to split.
    keys:       Explicit list of variable names to include in *matched*.
    predicate:  Callable ``(EnvVar) -> bool``; variables for which it returns
                ``True`` are placed in *matched*.

    Returns
    -------
    SplitResult with two child chains sharing the same profile.
    """
    if keys is not None and predicate is not None:
        raise ValueError("Provide either 'keys' or 'predicate', not both.")
    if keys is None and predicate is None:
        raise ValueError("One of 'keys' or 'predicate' is required.")

    if keys is not None:
        key_set = set(keys)
        _pred: Callable[[EnvVar], bool] = lambda v: v.key in key_set
    else:
        _pred = predicate  # type: ignore[assignment]

    matched_vars: Dict[str, EnvVar] = {}
    remainder_vars: Dict[str, EnvVar] = {}

    for var in chain.vars.values():
        if _pred(var):
            matched_vars[var.key] = var
        else:
            remainder_vars[var.key] = var

    matched_chain = EnvChain(profile=chain.profile)
    matched_chain.vars = matched_vars

    remainder_chain = EnvChain(profile=chain.profile)
    remainder_chain.vars = remainder_vars

    return SplitResult(
        profile=chain.profile,
        matched=matched_chain,
        remainder=remainder_chain,
    )
