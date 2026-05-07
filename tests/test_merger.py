"""Tests for envchain.merger module."""

import pytest
from envchain.chain import EnvChain
from envchain.merger import merge_chains, ConflictStrategy, MergeConflict


def _make_chain(**kwargs) -> EnvChain:
    """Helper: build an EnvChain with given key=default pairs."""
    chain = EnvChain()
    for key, value in kwargs.items():
        chain.add(key, default=value)
    return chain


class TestMergeChains:
    def test_raises_for_empty_list(self):
        with pytest.raises(ValueError, match="At least one"):
            merge_chains([])

    def test_single_chain_passthrough(self):
        chain = _make_chain(HOST="localhost", PORT="5432")
        merged = merge_chains([chain])
        assert merged.get("HOST") == "localhost"
        assert merged.get("PORT") == "5432"

    def test_non_overlapping_chains_merged(self):
        a = _make_chain(HOST="localhost")
        b = _make_chain(PORT="5432")
        merged = merge_chains([a, b])
        assert merged.get("HOST") == "localhost"
        assert merged.get("PORT") == "5432"

    def test_last_wins_strategy(self):
        a = _make_chain(HOST="localhost")
        b = _make_chain(HOST="remotehost")
        merged = merge_chains([a, b], strategy=ConflictStrategy.LAST_WINS)
        assert merged.get("HOST") == "remotehost"

    def test_first_wins_strategy(self):
        a = _make_chain(HOST="localhost")
        b = _make_chain(HOST="remotehost")
        merged = merge_chains([a, b], strategy=ConflictStrategy.FIRST_WINS)
        assert merged.get("HOST") == "localhost"

    def test_raise_strategy_on_conflict(self):
        a = _make_chain(HOST="localhost")
        b = _make_chain(HOST="remotehost")
        with pytest.raises(MergeConflict) as exc_info:
            merge_chains([a, b], strategy=ConflictStrategy.RAISE)
        assert exc_info.value.key == "HOST"
        assert "localhost" in exc_info.value.values
        assert "remotehost" in exc_info.value.values

    def test_raise_strategy_no_conflict_passes(self):
        a = _make_chain(HOST="localhost")
        b = _make_chain(HOST="localhost")  # same value, no conflict
        merged = merge_chains([a, b], strategy=ConflictStrategy.RAISE)
        assert merged.get("HOST") == "localhost"

    def test_none_values_handled_gracefully(self):
        a = _make_chain(HOST=None)
        b = _make_chain(HOST="remotehost")
        merged = merge_chains([a, b], strategy=ConflictStrategy.LAST_WINS)
        assert merged.get("HOST") == "remotehost"

    def test_all_none_values_remain_none(self):
        a = _make_chain(HOST=None)
        b = _make_chain(HOST=None)
        merged = merge_chains([a, b])
        assert merged.get("HOST") is None

    def test_three_chains_last_wins(self):
        a = _make_chain(DB="db1")
        b = _make_chain(DB="db2")
        c = _make_chain(DB="db3")
        merged = merge_chains([a, b, c], strategy=ConflictStrategy.LAST_WINS)
        assert merged.get("DB") == "db3"
