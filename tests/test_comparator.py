"""Tests for envchain.comparator."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.comparator import CompareEntry, CompareReport, compare_chains


def _make_chain(profile: str, **kwargs: str) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kwargs.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestCompareEntry:
    def test_equal_when_values_match(self):
        entry = CompareEntry(key="FOO", left_value="bar", right_value="bar")
        assert entry.is_equal is True

    def test_not_equal_when_values_differ(self):
        entry = CompareEntry(key="FOO", left_value="bar", right_value="baz")
        assert entry.is_equal is False

    def test_only_in_left(self):
        entry = CompareEntry(key="FOO", left_value="bar", right_value=None)
        assert entry.only_in_left is True
        assert entry.only_in_right is False

    def test_only_in_right(self):
        entry = CompareEntry(key="FOO", left_value=None, right_value="baz")
        assert entry.only_in_right is True
        assert entry.only_in_left is False

    def test_is_diverged(self):
        entry = CompareEntry(key="FOO", left_value="a", right_value="b")
        assert entry.is_diverged is True

    def test_not_diverged_when_one_side_missing(self):
        entry = CompareEntry(key="FOO", left_value=None, right_value="b")
        assert entry.is_diverged is False

    def test_repr(self):
        entry = CompareEntry(key="K", left_value="x", right_value="y")
        assert "K" in repr(entry)
        assert "x" in repr(entry)
        assert "y" in repr(entry)


class TestCompareReport:
    def test_is_identical_when_all_equal(self):
        left = _make_chain("dev", A="1", B="2")
        right = _make_chain("prod", A="1", B="2")
        report = compare_chains(left, right)
        assert report.is_identical is True

    def test_not_identical_when_values_differ(self):
        left = _make_chain("dev", A="1")
        right = _make_chain("prod", A="2")
        report = compare_chains(left, right)
        assert report.is_identical is False

    def test_diverged_keys_listed(self):
        left = _make_chain("dev", A="1", B="same")
        right = _make_chain("prod", A="2", B="same")
        report = compare_chains(left, right)
        assert report.diverged_keys == ["A"]

    def test_only_in_left_listed(self):
        left = _make_chain("dev", A="1", EXTRA="x")
        right = _make_chain("prod", A="1")
        report = compare_chains(left, right)
        assert "EXTRA" in report.only_in_left

    def test_only_in_right_listed(self):
        left = _make_chain("dev", A="1")
        right = _make_chain("prod", A="1", NEW="y")
        report = compare_chains(left, right)
        assert "NEW" in report.only_in_right

    def test_equal_keys_listed(self):
        left = _make_chain("dev", A="same", B="diff1")
        right = _make_chain("prod", A="same", B="diff2")
        report = compare_chains(left, right)
        assert "A" in report.equal_keys
        assert "B" not in report.equal_keys

    def test_profiles_stored(self):
        left = _make_chain("dev")
        right = _make_chain("prod")
        report = compare_chains(left, right)
        assert report.left_profile == "dev"
        assert report.right_profile == "prod"

    def test_repr_contains_profiles(self):
        left = _make_chain("dev", X="1")
        right = _make_chain("prod", X="2")
        report = compare_chains(left, right)
        r = repr(report)
        assert "dev" in r
        assert "prod" in r

    def test_entries_sorted_by_key(self):
        left = _make_chain("dev", Z="1", A="2", M="3")
        right = _make_chain("prod", Z="1", A="2", M="3")
        report = compare_chains(left, right)
        keys = [e.key for e in report.entries]
        assert keys == sorted(keys)
