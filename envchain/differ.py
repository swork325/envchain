"""Compare EnvChain profiles across environments to surface missing or mismatched keys."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from envchain.chain import EnvChain


@dataclass
class DiffEntry:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]

    @property
    def is_missing_left(self) -> bool:
        return self.left_value is None and self.right_value is not None

    @property
    def is_missing_right(self) -> bool:
        return self.left_value is not None and self.right_value is None

    @property
    def is_value_diff(self) -> bool:
        return (
            self.left_value is not None
            and self.right_value is not None
            and self.left_value != self.right_value
        )

    def __repr__(self) -> str:
        return (
            f"DiffEntry(key={self.key!r}, "
            f"left={self.left_value!r}, right={self.right_value!r})"
        )


@dataclass
class ChainDiff:
    left_name: str
    right_name: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.entries)

    def missing_in_left(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.is_missing_left]

    def missing_in_right(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.is_missing_right]

    def value_diffs(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.is_value_diff]

    def summary(self) -> str:
        lines = [f"Diff: {self.left_name} vs {self.right_name}"]
        if not self.has_differences:
            lines.append("  No differences found.")
            return "\n".join(lines)
        for e in self.missing_in_left():
            lines.append(f"  + {e.key} (only in {self.right_name}: {e.right_value!r})")
        for e in self.missing_in_right():
            lines.append(f"  - {e.key} (only in {self.left_name}: {e.left_value!r})")
        for e in self.value_diffs():
            lines.append(
                f"  ~ {e.key} ({self.left_name}: {e.left_value!r} | "
                f"{self.right_name}: {e.right_value!r})"
            )
        return "\n".join(lines)


def diff_chains(
    left: EnvChain,
    right: EnvChain,
    left_name: str = "left",
    right_name: str = "right",
    compare_values: bool = False,
) -> ChainDiff:
    """Compare two EnvChain instances and return a ChainDiff.

    Args:
        left: First EnvChain to compare.
        right: Second EnvChain to compare.
        left_name: Label for the left chain.
        right_name: Label for the right chain.
        compare_values: If True, also report keys present in both but with
                        different resolved values.
    """
    left_keys: Set[str] = set(left.keys())
    right_keys: Set[str] = set(right.keys())
    all_keys = left_keys | right_keys

    entries: List[DiffEntry] = []
    for key in sorted(all_keys):
        lv = left.get(key) if key in left_keys else None
        rv = right.get(key) if key in right_keys else None

        if lv is None and rv is not None:
            entries.append(DiffEntry(key=key, left_value=None, right_value=rv))
        elif lv is not None and rv is None:
            entries.append(DiffEntry(key=key, left_value=lv, right_value=None))
        elif compare_values and lv != rv:
            entries.append(DiffEntry(key=key, left_value=lv, right_value=rv))

    return ChainDiff(left_name=left_name, right_name=right_name, entries=entries)
