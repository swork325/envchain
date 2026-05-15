"""Assign and query free-form labels (key/value metadata) on EnvVar entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envchain.chain import EnvChain, EnvVar


@dataclass
class LabeledVar:
    """An EnvVar decorated with an arbitrary label mapping."""

    var: EnvVar
    labels: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"LabeledVar(key={self.var.key!r}, labels={self.labels!r})"

    def get(self, label: str) -> Optional[str]:
        """Return the value of *label*, or ``None`` if absent."""
        return self.labels.get(label)

    def has_label(self, label: str) -> bool:
        """Return ``True`` when *label* is present (any value)."""
        return label in self.labels


@dataclass
class LabelReport:
    """Collection of LabeledVar entries produced by :func:`label_chain`."""

    profile: str
    entries: List[LabeledVar] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"LabelReport(profile={self.profile!r}, entries={len(self.entries)})"

    def where(self, label: str, value: str) -> List[LabeledVar]:
        """Return entries whose *label* equals *value*."""
        return [e for e in self.entries if e.get(label) == value]

    def keys_with(self, label: str) -> List[str]:
        """Return the keys of all entries that carry *label*."""
        return [e.var.key for e in self.entries if e.has_label(label)]


def label_chain(
    chain: EnvChain,
    rules: Dict[str, Dict[str, str]],
) -> LabelReport:
    """Attach labels to every variable in *chain* according to *rules*.

    *rules* maps a variable key to a dict of ``{label: value}`` pairs.  Keys
    not mentioned in *rules* receive an empty label mapping.
    """
    entries: List[LabeledVar] = []
    for var in chain.vars:
        labels = dict(rules.get(var.key, {}))
        entries.append(LabeledVar(var=var, labels=labels))
    return LabelReport(profile=chain.profile, entries=entries)
