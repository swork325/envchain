"""Score EnvChain health based on completeness and value quality."""

from dataclasses import dataclass, field
from typing import List

from envchain.chain import EnvChain


SCORE_KEYS = ["completeness", "defaults_ratio", "non_empty_ratio"]


@dataclass
class ScoreReport:
    profile: str
    total: int
    resolved: int
    defaulted: int
    empty: int
    scores: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"ScoreReport(profile={self.profile!r}, total={self.total}, "
            f"resolved={self.resolved}, defaulted={self.defaulted}, "
            f"empty={self.empty}, scores={self.scores})"
        )

    @property
    def overall(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(self.scores.values()) / len(self.scores), 4)


def score_chain(chain: EnvChain) -> ScoreReport:
    """Compute a health score for the given EnvChain."""
    vars_ = list(chain)
    total = len(vars_)

    if total == 0:
        return ScoreReport(
            profile=chain.profile,
            total=0,
            resolved=0,
            defaulted=0,
            empty=0,
            scores={k: 0.0 for k in SCORE_KEYS},
        )

    resolved = sum(1 for v in vars_ if v.value is not None)
    defaulted = sum(1 for v in vars_ if v.value is not None and v.default == v.value)
    empty = sum(1 for v in vars_ if v.value == "")

    completeness = round(resolved / total, 4)
    defaults_ratio = round(1.0 - (defaulted / total), 4)
    non_empty_ratio = round((resolved - empty) / total, 4) if resolved else 0.0

    scores = {
        "completeness": completeness,
        "defaults_ratio": defaults_ratio,
        "non_empty_ratio": non_empty_ratio,
    }

    return ScoreReport(
        profile=chain.profile,
        total=total,
        resolved=resolved,
        defaulted=defaulted,
        empty=empty,
        scores=scores,
    )
