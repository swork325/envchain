"""Group EnvChain variables by prefix or custom classifier."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


class EnvGroup:
    """A named collection of EnvVar entries."""

    def __init__(self, name: str, vars: List[EnvVar]) -> None:
        self.name = name
        self.vars = vars

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvGroup(name={self.name!r}, vars={len(self.vars)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnvGroup):
            return NotImplemented
        return self.name == other.name and self.vars == other.vars


def group_by_prefix(
    chain: EnvChain,
    separator: str = "_",
    ungrouped_label: str = "__other__",
) -> Dict[str, EnvGroup]:
    """Group variables by the first segment of their key before *separator*.

    Variables whose key contains no separator are placed in *ungrouped_label*.
    """
    buckets: Dict[str, List[EnvVar]] = defaultdict(list)
    for var in chain._vars.values():
        if separator in var.key:
            prefix = var.key.split(separator, 1)[0]
        else:
            prefix = ungrouped_label
        buckets[prefix].append(var)

    return {name: EnvGroup(name, vars) for name, vars in sorted(buckets.items())}


def group_by_classifier(
    chain: EnvChain,
    classifier: Callable[[EnvVar], Optional[str]],
    ungrouped_label: str = "__other__",
) -> Dict[str, EnvGroup]:
    """Group variables using an arbitrary *classifier* callable.

    The callable receives an :class:`EnvVar` and should return a group name
    string, or ``None`` to place the variable in *ungrouped_label*.
    """
    buckets: Dict[str, List[EnvVar]] = defaultdict(list)
    for var in chain._vars.values():
        label = classifier(var)
        if label is None:
            label = ungrouped_label
        buckets[label].append(var)

    return {name: EnvGroup(name, vars) for name, vars in sorted(buckets.items())}
