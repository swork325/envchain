"""Summarize an EnvChain into a human-readable or machine-readable report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envchain.chain import EnvChain


@dataclass
class SummaryReport:
    profile: str
    total: int
    resolved: int
    defaulted: int
    missing: int
    keys: List[str] = field(default_factory=list)
    missing_keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SummaryReport(profile={self.profile!r}, total={self.total}, "
            f"resolved={self.resolved}, defaulted={self.defaulted}, "
            f"missing={self.missing})"
        )

    def to_dict(self) -> Dict:
        return {
            "profile": self.profile,
            "total": self.total,
            "resolved": self.resolved,
            "defaulted": self.defaulted,
            "missing": self.missing,
            "keys": self.keys,
            "missing_keys": self.missing_keys,
        }


def summarize_chain(chain: EnvChain) -> SummaryReport:
    """Produce a SummaryReport describing the state of all variables in *chain*."""
    resolved = 0
    defaulted = 0
    missing = 0
    keys: List[str] = []
    missing_keys: List[str] = []

    for var in chain._vars.values():
        keys.append(var.key)
        value = var.resolve()
        if value is None:
            missing += 1
            missing_keys.append(var.key)
        elif var.resolve() == var.default and var.default is not None:
            defaulted += 1
        else:
            resolved += 1

    total = resolved + defaulted + missing

    return SummaryReport(
        profile=chain.profile,
        total=total,
        resolved=resolved,
        defaulted=defaulted,
        missing=missing,
        keys=sorted(keys),
        missing_keys=sorted(missing_keys),
    )
