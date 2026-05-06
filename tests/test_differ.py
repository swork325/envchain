"""Tests for envchain.differ — chain diffing feature."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.differ import ChainDiff, DiffEntry, diff_chains


def _make_chain(**kwargs: str) -> EnvChain:
    """Build an EnvChain with static default values for testing."""
    chain = EnvChain()
    for key, value in kwargs.items():
        chain.add(EnvVar(name=key, default=value))
    return chain


class TestDiffEntry:
    def test_missing_left(self):
        entry = DiffEntry(key="FOO", left_value=None, right_value="bar")
        assert entry.is_missing_left is True
        assert entry.is_missing_right is False
        assert entry.is_value_diff is False

    def test_missing_right(self):
        entry = DiffEntry(key="FOO", left_value="bar", right_value=None)
        assert entry.is_missing_left is False
        assert entry.is_missing_right is True
        assert entry.is_value_diff is False

    def test_value_diff(self):
        entry = DiffEntry(key="FOO", left_value="a", right_value="b")
        assert entry.is_value_diff is True
        assert entry.is_missing_left is False
        assert entry.is_missing_right is False

    def test_repr(self):
        entry = DiffEntry(key="X", left_value="1", right_value="2")
        assert "X" in repr(entry)
        assert "1" in repr(entry)
        assert "2" in repr(entry)


class TestDiffChains:
    def test_no_differences_when_identical_keys(self):
        left = _make_chain(DB_URL="postgres://localhost", SECRET="abc")
        right = _make_chain(DB_URL="postgres://localhost", SECRET="abc")
        result = diff_chains(left, right)
        assert result.has_differences is False
        assert result.entries == []

    def test_detects_key_missing_in_right(self):
        left = _make_chain(ONLY_LEFT="val", SHARED="x")
        right = _make_chain(SHARED="x")
        result = diff_chains(left, right, left_name="dev", right_name="prod")
        assert result.has_differences is True
        missing = result.missing_in_right()
        assert len(missing) == 1
        assert missing[0].key == "ONLY_LEFT"

    def test_detects_key_missing_in_left(self):
        left = _make_chain(SHARED="x")
        right = _make_chain(ONLY_RIGHT="val", SHARED="x")
        result = diff_chains(left, right)
        missing = result.missing_in_left()
        assert len(missing) == 1
        assert missing[0].key == "ONLY_RIGHT"

    def test_compare_values_off_by_default(self):
        left = _make_chain(KEY="value_a")
        right = _make_chain(KEY="value_b")
        result = diff_chains(left, right)
        # same keys present on both sides — no structural diff without compare_values
        assert result.has_differences is False

    def test_compare_values_on_reports_mismatch(self):
        left = _make_chain(KEY="value_a")
        right = _make_chain(KEY="value_b")
        result = diff_chains(left, right, compare_values=True)
        assert result.has_differences is True
        diffs = result.value_diffs()
        assert len(diffs) == 1
        assert diffs[0].key == "KEY"
        assert diffs[0].left_value == "value_a"
        assert diffs[0].right_value == "value_b"

    def test_summary_no_differences(self):
        left = _make_chain(A="1")
        right = _make_chain(A="1")
        summary = diff_chains(left, right, left_name="dev", right_name="prod").summary()
        assert "No differences" in summary
        assert "dev" in summary
        assert "prod" in summary

    def test_summary_with_differences(self):
        left = _make_chain(ONLY_DEV="x", SHARED="y")
        right = _make_chain(ONLY_PROD="z", SHARED="y")
        summary = diff_chains(left, right, left_name="dev", right_name="prod").summary()
        assert "ONLY_DEV" in summary
        assert "ONLY_PROD" in summary
        assert "dev" in summary
        assert "prod" in summary

    def test_keys_sorted_in_entries(self):
        left = _make_chain(ZEBRA="1", ALPHA="2")
        right = _make_chain(ALPHA="2")
        result = diff_chains(left, right)
        keys = [e.key for e in result.entries]
        assert keys == sorted(keys)
