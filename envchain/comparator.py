"""Compare two EnvChains and produce a structured comparison report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envchain.chain import EnvChain


@dataclass
class CompareEntry:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]

    @property
    def is_equal(self) -> bool:
        return self.left_value == self.right_value

    @property
    def only_in_left(self) -> bool:
        return self.left_value is not None and self.right_value is None

    @property
    def only_in_right(self) -> bool:
        return self.left_value is None and self.right_value is not None

    @property
    def is_diverged(self) -> bool:
        return (
            self.left_value is not None
            and self.right_value is not None
            and self.left_value != self.right_value
        )

    def __repr__(self) -> str:
        return (
            f"CompareEntry(key={self.key!r}, "
            f"left={self.left_value!r}, right={self.right_value!r})"
        )


@dataclass
class CompareReport:
    left_profile: str
    right_profile: str
    entries: List[CompareEntry] = field(default_factory=list)

    @property
    def equal_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_equal]

    @property
    def diverged_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_diverged]

    @property
    def only_in_left(self) -> List[str]:
        return [e.key for e in self.entries if e.only_in_left]

    @property
    def only_in_right(self) -> List[str]:
        return [e.key for e in self.entries if e.only_in_right]

    @property
    def is_identical(self) -> bool:
        return all(e.is_equal for e in self.entries)

    def __repr__(self) -> str:
        return (
            f"CompareReport(left={self.left_profile!r}, "
            f"right={self.right_profile!r}, "
            f"equal={len(self.equal_keys)}, "
            f"diverged={len(self.diverged_keys)})"
        )


def compare_chains(left: EnvChain, right: EnvChain) -> CompareReport:
    """Compare two EnvChains key-by-key and return a CompareReport."""
    all_keys = sorted(set(left._vars) | set(right._vars))
    entries = [
        CompareEntry(
            key=key,
            left_value=left._vars[key].resolve() if key in left._vars else None,
            right_value=right._vars[key].resolve() if key in right._vars else None,
        )
        for key in all_keys
    ]
    return CompareReport(
        left_profile=left.profile,
        right_profile=right.profile,
        entries=entries,
    )
