"""Variable interpolation for EnvChain — resolves ${VAR} references within values."""

from __future__ import annotations

import re
from typing import Optional

from envchain.chain import EnvChain

_REF_PATTERN = re.compile(r"\$\{([^}]+)\}")


class InterpolationError(Exception):
    """Raised when a referenced variable cannot be resolved during interpolation."""

    def __init__(self, key: str, ref: str) -> None:
        self.key = key
        self.ref = ref
        super().__init__(f"Variable '{key}' references undefined key '${{{ref}}}'")


def _resolve_refs(
    value: str,
    chain: EnvChain,
    source_key: str,
    strict: bool,
) -> str:
    """Replace all ${REF} tokens in *value* using *chain* as the lookup source."""

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        ref_key = match.group(1)
        resolved = chain.get(ref_key)
        if resolved is None:
            if strict:
                raise InterpolationError(source_key, ref_key)
            return match.group(0)  # leave token unchanged
        return resolved

    return _REF_PATTERN.sub(_replace, value)


def interpolate_chain(
    chain: EnvChain,
    strict: bool = True,
    max_passes: int = 5,
) -> EnvChain:
    """Return a new EnvChain with all ${VAR} references expanded.

    Parameters
    ----------
    chain:
        Source chain whose values may contain ``${KEY}`` references.
    strict:
        When *True* (default) an :class:`InterpolationError` is raised for
        unresolvable references.  When *False* unresolvable tokens are left
        as-is.
    max_passes:
        Maximum number of expansion rounds (handles nested references).
    """
    result = EnvChain(profile=chain.profile)
    for var in chain._vars.values():  # noqa: SLF001
        result.add(var.key, var.value, var.default, var.required)

    for _ in range(max_passes):
        changed = False
        for var in result._vars.values():  # noqa: SLF001
            raw = var.value
            if raw is None or _REF_PATTERN.search(raw) is None:
                continue
            expanded = _resolve_refs(raw, result, var.key, strict)
            if expanded != raw:
                var.value = expanded
                changed = True
        if not changed:
            break

    return result
