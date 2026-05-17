"""Tests for envchain.trimmer."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.trimmer import TrimResult, trim_chain


def _make_chain(*pairs: tuple[str, str | None], profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in pairs:
        chain.add(EnvVar(key=key, default=value))
    return chain


# ---------------------------------------------------------------------------
# TrimResult unit tests
# ---------------------------------------------------------------------------

class TestTrimResult:
    def test_repr_contains_profile_and_counts(self):
        r = TrimResult(profile="dev")
        r.kept = [object(), object()]  # type: ignore[list-item]
        r.dropped = [object()]  # type: ignore[list-item]
        assert "dev" in repr(r)
        assert "kept=2" in repr(r)
        assert "dropped=1" in repr(r)

    def test_is_clean_when_nothing_dropped(self):
        r = TrimResult(profile="staging")
        assert r.is_clean is True

    def test_not_clean_when_something_dropped(self):
        r = TrimResult(profile="staging")
        r.dropped.append(EnvVar(key="X", default="v"))
        assert r.is_clean is False

    def test_to_chain_contains_kept_vars(self):
        chain = _make_chain(("A", "1"), ("B", "2"), ("C", "3"))
        result = trim_chain(chain, max_keys=2)
        trimmed = result.to_chain()
        keys = [v.key for v in trimmed.vars]
        assert keys == ["A", "B"]

    def test_to_chain_profile_preserved(self):
        chain = _make_chain(("A", "1"), profile="prod")
        result = trim_chain(chain)
        assert result.to_chain().profile == "prod"


# ---------------------------------------------------------------------------
# trim_chain — max_keys
# ---------------------------------------------------------------------------

class TestTrimChainMaxKeys:
    def test_no_constraint_keeps_all(self):
        chain = _make_chain(("A", "1"), ("B", "2"), ("C", "3"))
        result = trim_chain(chain)
        assert len(result.kept) == 3
        assert len(result.dropped) == 0

    def test_max_keys_limits_kept(self):
        chain = _make_chain(("A", "1"), ("B", "2"), ("C", "3"))
        result = trim_chain(chain, max_keys=2)
        assert len(result.kept) == 2
        assert len(result.dropped) == 1

    def test_max_keys_zero_drops_all(self):
        chain = _make_chain(("A", "1"), ("B", "2"))
        result = trim_chain(chain, max_keys=0)
        assert result.kept == []
        assert len(result.dropped) == 2

    def test_max_keys_larger_than_chain_keeps_all(self):
        chain = _make_chain(("A", "1"), ("B", "2"))
        result = trim_chain(chain, max_keys=100)
        assert len(result.kept) == 2


# ---------------------------------------------------------------------------
# trim_chain — max_value_length
# ---------------------------------------------------------------------------

class TestTrimChainMaxValueLength:
    def test_drops_long_values(self):
        chain = _make_chain(("SHORT", "hi"), ("LONG", "a" * 20))
        result = trim_chain(chain, max_value_length=5)
        assert len(result.kept) == 1
        assert result.kept[0].key == "SHORT"

    def test_keeps_value_exactly_at_limit(self):
        chain = _make_chain(("K", "hello"))
        result = trim_chain(chain, max_value_length=5)
        assert len(result.kept) == 1

    def test_none_value_not_dropped_by_length(self):
        chain = _make_chain(("MISSING", None))
        result = trim_chain(chain, max_value_length=3)
        assert len(result.kept) == 1


# ---------------------------------------------------------------------------
# trim_chain — drop_empty
# ---------------------------------------------------------------------------

class TestTrimChainDropEmpty:
    def test_drops_none_values(self):
        chain = _make_chain(("A", None), ("B", "ok"))
        result = trim_chain(chain, drop_empty=True)
        assert len(result.kept) == 1
        assert result.kept[0].key == "B"

    def test_drops_empty_string_values(self):
        chain = _make_chain(("A", ""), ("B", "val"))
        result = trim_chain(chain, drop_empty=True)
        assert len(result.kept) == 1

    def test_keeps_whitespace_only_values(self):
        chain = _make_chain(("A", "  "))
        result = trim_chain(chain, drop_empty=True)
        assert len(result.kept) == 1
