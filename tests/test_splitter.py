"""Tests for envchain.splitter."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.splitter import SplitResult, split_chain


def _make_chain(*pairs: tuple, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in pairs:
        chain.add(EnvVar(key=key, default=value))
    return chain


# ---------------------------------------------------------------------------
# TestSplitResult
# ---------------------------------------------------------------------------

class TestSplitResult:
    def test_is_empty_when_no_match(self):
        chain = _make_chain(("A", "1"), ("B", "2"))
        result = split_chain(chain, keys=[])
        assert result.is_empty()

    def test_not_empty_when_matched(self):
        chain = _make_chain(("A", "1"), ("B", "2"))
        result = split_chain(chain, keys=["A"])
        assert not result.is_empty()

    def test_repr_contains_profile_and_counts(self):
        chain = _make_chain(("X", "1"), ("Y", "2"), ("Z", "3"))
        result = split_chain(chain, keys=["X", "Z"])
        r = repr(result)
        assert "dev" in r
        assert "matched=2" in r
        assert "remainder=1" in r


# ---------------------------------------------------------------------------
# TestSplitChainByKeys
# ---------------------------------------------------------------------------

class TestSplitChainByKeys:
    def test_matched_contains_requested_keys(self):
        chain = _make_chain(("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("APP_KEY", "secret"))
        result = split_chain(chain, keys=["DB_HOST", "DB_PORT"])
        assert set(result.matched.vars.keys()) == {"DB_HOST", "DB_PORT"}

    def test_remainder_contains_remaining_keys(self):
        chain = _make_chain(("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("APP_KEY", "secret"))
        result = split_chain(chain, keys=["DB_HOST", "DB_PORT"])
        assert set(result.remainder.vars.keys()) == {"APP_KEY"}

    def test_unknown_keys_are_silently_ignored(self):
        chain = _make_chain(("A", "1"))
        result = split_chain(chain, keys=["A", "NONEXISTENT"])
        assert set(result.matched.vars.keys()) == {"A"}
        assert result.remainder.vars == {}

    def test_profile_preserved_on_both_children(self):
        chain = _make_chain(("A", "1"), profile="staging")
        result = split_chain(chain, keys=["A"])
        assert result.matched.profile == "staging"
        assert result.remainder.profile == "staging"


# ---------------------------------------------------------------------------
# TestSplitChainByPredicate
# ---------------------------------------------------------------------------

class TestSplitChainByPredicate:
    def test_predicate_filters_by_prefix(self):
        chain = _make_chain(("DB_HOST", "h"), ("DB_PORT", "5432"), ("APP_KEY", "k"))
        result = split_chain(chain, predicate=lambda v: v.key.startswith("DB_"))
        assert set(result.matched.vars.keys()) == {"DB_HOST", "DB_PORT"}
        assert set(result.remainder.vars.keys()) == {"APP_KEY"}

    def test_predicate_filters_by_value_presence(self):
        chain = _make_chain(("SET", "value"), ("EMPTY", None))
        result = split_chain(chain, predicate=lambda v: v.default is not None)
        assert "SET" in result.matched.vars
        assert "EMPTY" in result.remainder.vars


# ---------------------------------------------------------------------------
# TestSplitChainErrors
# ---------------------------------------------------------------------------

class TestSplitChainErrors:
    def test_raises_when_neither_keys_nor_predicate(self):
        chain = _make_chain(("A", "1"))
        with pytest.raises(ValueError, match="required"):
            split_chain(chain)

    def test_raises_when_both_keys_and_predicate(self):
        chain = _make_chain(("A", "1"))
        with pytest.raises(ValueError, match="not both"):
            split_chain(chain, keys=["A"], predicate=lambda v: True)
