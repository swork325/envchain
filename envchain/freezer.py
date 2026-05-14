"""Freeze and restore EnvChain state to/from immutable snapshots with diff awareness."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.chain import EnvChain, EnvVar
from envchain.differ import diff_chains, DiffEntry


@dataclass
class FrozenChain:
    """An immutable record of an EnvChain's resolved values at a point in time."""

    profile: str
    values: Dict[str, Optional[str]] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"FrozenChain(profile={self.profile!r}, keys={list(self.values.keys())})"

    def to_dict(self) -> dict:
        return {"profile": self.profile, "values": self.values}

    @classmethod
    def from_dict(cls, data: dict) -> "FrozenChain":
        return cls(profile=data["profile"], values=data["values"])

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "FrozenChain":
        return cls.from_dict(json.loads(text))


def freeze(chain: EnvChain, profile: str = "default") -> FrozenChain:
    """Capture the current resolved state of *chain* into a FrozenChain."""
    values: Dict[str, Optional[str]] = {
        var.key: var.resolve() for var in chain._vars
    }
    return FrozenChain(profile=profile, values=values)


def thaw(frozen: FrozenChain) -> EnvChain:
    """Reconstruct an EnvChain from a FrozenChain (values become defaults)."""
    chain = EnvChain()
    for key, value in frozen.values.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


def diff_frozen(
    before: FrozenChain, after: FrozenChain
) -> List[DiffEntry]:
    """Return the diff between two FrozenChain instances."""
    return diff_chains(thaw(before), thaw(after))
