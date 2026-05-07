"""Merge multiple EnvChains with configurable conflict resolution strategies."""

from enum import Enum
from typing import Dict, List, Optional
from envchain.chain import EnvChain


class ConflictStrategy(Enum):
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    RAISE = "raise"


class MergeConflict(Exception):
    """Raised when a key conflict is detected and strategy is RAISE."""

    def __init__(self, key: str, values: List[Optional[str]]):
        self.key = key
        self.values = values
        super().__init__(
            f"Conflict on key '{key}': found values {values}"
        )


def merge_chains(
    chains: List[EnvChain],
    strategy: ConflictStrategy = ConflictStrategy.LAST_WINS,
) -> EnvChain:
    """Merge a list of EnvChains into a single EnvChain.

    Args:
        chains: Ordered list of EnvChain instances to merge.
        strategy: How to handle key conflicts across chains.

    Returns:
        A new EnvChain containing the merged variables.

    Raises:
        MergeConflict: If strategy is RAISE and a conflicting key is found.
        ValueError: If chains list is empty.
    """
    if not chains:
        raise ValueError("At least one EnvChain must be provided for merging.")

    seen: Dict[str, List[Optional[str]]] = {}

    for chain in chains:
        for var in chain._vars:
            value = var.resolve()
            if var.name not in seen:
                seen[var.name] = []
            seen[var.name].append(value)

    result = EnvChain()

    for key, values in seen.items():
        non_none = [v for v in values if v is not None]

        if len(set(v for v in values if v is not None)) > 1:
            if strategy == ConflictStrategy.RAISE:
                raise MergeConflict(key, values)
            elif strategy == ConflictStrategy.FIRST_WINS:
                chosen = non_none[0] if non_none else None
            else:  # LAST_WINS
                chosen = non_none[-1] if non_none else None
        else:
            chosen = non_none[0] if non_none else None

        result.add(key, default=chosen)

    return result
