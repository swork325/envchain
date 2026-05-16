"""Normalize environment variable keys and values within a chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class NormalizeResult:
    """Result of a normalization pass over an EnvChain."""

    profile: str
    original: EnvChain
    normalized: EnvChain
    renamed_keys: List[tuple] = field(default_factory=list)   # [(old, new), ...]
    coerced_values: List[str] = field(default_factory=list)   # keys whose values changed

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"NormalizeResult(profile={self.profile!r}, "
            f"renamed={len(self.renamed_keys)}, "
            f"coerced={len(self.coerced_values)})"
        )

    @property
    def is_clean(self) -> bool:
        """True when no renames or value coercions were necessary."""
        return not self.renamed_keys and not self.coerced_values


def normalize_chain(
    chain: EnvChain,
    *,
    uppercase_keys: bool = True,
    strip_values: bool = True,
    replace_spaces_in_keys: bool = True,
    space_replacement: str = "_",
) -> NormalizeResult:
    """Return a new EnvChain with normalized keys and values.

    Parameters
    ----------
    chain:
        Source chain to normalize.
    uppercase_keys:
        Convert all variable keys to upper-case.
    strip_values:
        Strip leading/trailing whitespace from resolved values.
    replace_spaces_in_keys:
        Replace spaces in keys with *space_replacement*.
    space_replacement:
        Character used when replacing spaces in keys.
    """
    renamed_keys: List[tuple] = []
    coerced_values: List[str] = []
    new_vars: List[EnvVar] = []

    for var in chain.vars:
        original_key = var.key
        new_key = original_key

        if replace_spaces_in_keys:
            new_key = new_key.replace(" ", space_replacement)
        if uppercase_keys:
            new_key = new_key.upper()

        if new_key != original_key:
            renamed_keys.append((original_key, new_key))

        original_value: Optional[str] = var.default
        new_default = original_value
        if strip_values and isinstance(original_value, str):
            new_default = original_value.strip()
            if new_default != original_value:
                coerced_values.append(new_key)

        new_vars.append(EnvVar(key=new_key, default=new_default))

    normalized = EnvChain(profile=chain.profile)
    for v in new_vars:
        normalized.add(v)

    return NormalizeResult(
        profile=chain.profile,
        original=chain,
        normalized=normalized,
        renamed_keys=renamed_keys,
        coerced_values=coerced_values,
    )
