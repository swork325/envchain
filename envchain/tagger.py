"""Tag environment variables with arbitrary labels and filter/query by tag."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List

from envchain.chain import EnvChain, EnvVar


@dataclass
class TaggedVar:
    """An EnvVar paired with a set of tags."""

    var: EnvVar
    tags: FrozenSet[str] = field(default_factory=frozenset)

    def __repr__(self) -> str:
        tag_str = ", ".join(sorted(self.tags))
        return f"TaggedVar(key={self.var.key!r}, tags={{{tag_str}}})"

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


class EnvTagger:
    """Attach tags to keys in an EnvChain and query by tag."""

    def __init__(self, chain: EnvChain) -> None:
        self._chain = chain
        self._tagged: Dict[str, TaggedVar] = {}
        for var in chain.vars:
            self._tagged[var.key] = TaggedVar(var=var)

    def tag(self, key: str, *tags: str) -> "EnvTagger":
        """Add one or more tags to a key. Raises KeyError if key not in chain."""
        if key not in self._tagged:
            raise KeyError(f"Key {key!r} not found in chain")
        existing = self._tagged[key].tags
        self._tagged[key] = TaggedVar(
            var=self._tagged[key].var,
            tags=existing | frozenset(tags),
        )
        return self

    def tag_all(self, keys: Iterable[str], *tags: str) -> "EnvTagger":
        """Convenience method to tag multiple keys at once."""
        for key in keys:
            self.tag(key, *tags)
        return self

    def get_tags(self, key: str) -> FrozenSet[str]:
        """Return the tags associated with a key."""
        if key not in self._tagged:
            raise KeyError(f"Key {key!r} not found in chain")
        return self._tagged[key].tags

    def filter_by_tag(self, tag: str) -> List[TaggedVar]:
        """Return all TaggedVars that carry the given tag."""
        return [tv for tv in self._tagged.values() if tv.has_tag(tag)]

    def all_tags(self) -> FrozenSet[str]:
        """Return the union of all tags across every variable."""
        result: FrozenSet[str] = frozenset()
        for tv in self._tagged.values():
            result = result | tv.tags
        return result

    def tagged_vars(self) -> List[TaggedVar]:
        """Return all TaggedVar entries in insertion order."""
        return list(self._tagged.values())
