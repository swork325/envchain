"""Promote environment variable chains between profiles (e.g. dev -> staging -> prod)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain
from envchain.profiles import KNOWN_PROFILES


_PROMOTION_ORDER: List[str] = ["dev", "staging", "prod"]


@dataclass
class PromotionResult:
    source_profile: str
    target_profile: str
    promoted_keys: List[str]
    skipped_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PromotionResult(source={self.source_profile!r}, "
            f"target={self.target_profile!r}, "
            f"promoted={len(self.promoted_keys)}, "
            f"skipped={len(self.skipped_keys)})"
        )

    @property
    def is_empty(self) -> bool:
        return len(self.promoted_keys) == 0


def next_profile(profile: str) -> Optional[str]:
    """Return the next profile in the promotion chain, or None if already at end."""
    try:
        idx = _PROMOTION_ORDER.index(profile)
    except ValueError:
        raise ValueError(
            f"Unknown profile {profile!r}. Known order: {_PROMOTION_ORDER}"
        )
    if idx + 1 >= len(_PROMOTION_ORDER):
        return None
    return _PROMOTION_ORDER[idx + 1]


def promote_chain(
    source: EnvChain,
    target: EnvChain,
    *,
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
) -> tuple[EnvChain, PromotionResult]:
    """Promote variables from *source* into *target*.

    Args:
        source: The chain to promote values from.
        target: The chain to promote values into.
        overwrite: When True, existing keys in target are overwritten.
        keys: Optional explicit list of keys to promote; defaults to all resolved
              keys in source.

    Returns:
        A new EnvChain with promoted values applied, and a PromotionResult.
    """
    source_vars = {v.key: v for v in source.vars}
    target_vars = {v.key: v for v in target.vars}

    candidates = list(keys) if keys is not None else list(source_vars.keys())

    promoted: List[str] = []
    skipped: List[str] = []

    new_chain = EnvChain(profile=target.profile)
    # Copy existing target vars first
    for v in target.vars:
        new_chain.add(v)

    for key in candidates:
        if key not in source_vars:
            skipped.append(key)
            continue
        src_var = source_vars[key]
        resolved = src_var.resolve()
        if resolved is None:
            skipped.append(key)
            continue
        if key in target_vars and not overwrite:
            skipped.append(key)
            continue
        from envchain.chain import EnvVar
        new_chain.vars = [v for v in new_chain.vars if v.key != key]
        new_chain.add(EnvVar(key=key, default=resolved))
        promoted.append(key)

    result = PromotionResult(
        source_profile=source.profile,
        target_profile=target.profile,
        promoted_keys=promoted,
        skipped_keys=skipped,
    )
    return new_chain, result
