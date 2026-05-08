"""Utilities for sorting EnvChain variables by various criteria."""

from __future__ import annotations

from enum import Enum
from typing import Callable

from envchain.chain import EnvChain, EnvVar


class SortKey(str, Enum):
    NAME = "name"
    VALUE = "value"
    HAS_DEFAULT = "has_default"
    IS_SET = "is_set"


SUPPORTED_SORT_KEYS = [k.value for k in SortKey]


def _key_fn(sort_key: SortKey, reverse: bool) -> Callable[[EnvVar], object]:
    if sort_key == SortKey.NAME:
        return lambda v: v.name.lower()
    if sort_key == SortKey.VALUE:
        # None values sort last when ascending, first when descending
        resolved = lambda v: v.resolve()  # noqa: E731
        return lambda v: (resolved(v) is None, resolved(v) or "")
    if sort_key == SortKey.HAS_DEFAULT:
        return lambda v: (v.default is None, v.name.lower())
    if sort_key == SortKey.IS_SET:
        return lambda v: (v.resolve() is None, v.name.lower())
    raise ValueError(f"Unknown sort key: {sort_key!r}")


def sort_chain(
    chain: EnvChain,
    by: str = SortKey.NAME,
    reverse: bool = False,
) -> EnvChain:
    """Return a new EnvChain with variables sorted by *by*.

    Parameters
    ----------
    chain:   Source EnvChain whose variables are sorted.
    by:      One of the :class:`SortKey` values (default ``"name"``).
    reverse: When ``True`` the sort order is reversed.

    Returns
    -------
    A fresh :class:`EnvChain` containing the same :class:`EnvVar` objects in
    the requested order.
    """
    try:
        key = SortKey(by)
    except ValueError:
        raise ValueError(
            f"Unsupported sort key {by!r}. "
            f"Choose one of: {SUPPORTED_SORT_KEYS}"
        )

    sorted_vars = sorted(chain.vars, key=_key_fn(key, reverse), reverse=reverse)
    new_chain = EnvChain(profile=chain.profile)
    for var in sorted_vars:
        new_chain.add(var)
    return new_chain
