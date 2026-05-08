"""Tests for envchain.sorter."""

from __future__ import annotations

import os
import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.sorter import sort_chain, SUPPORTED_SORT_KEYS


def _make_chain(*vars_: EnvVar, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for v in vars_:
        chain.add(v)
    return chain


class TestSupportedSortKeys:
    def test_contains_name(self):
        assert "name" in SUPPORTED_SORT_KEYS

    def test_contains_value(self):
        assert "value" in SUPPORTED_SORT_KEYS

    def test_contains_has_default(self):
        assert "has_default" in SUPPORTED_SORT_KEYS

    def test_contains_is_set(self):
        assert "is_set" in SUPPORTED_SORT_KEYS


class TestSortByName:
    def test_ascending(self):
        chain = _make_chain(
            EnvVar("ZEBRA"), EnvVar("ALPHA"), EnvVar("MANGO")
        )
        result = sort_chain(chain, by="name")
        assert [v.name for v in result.vars] == ["ALPHA", "MANGO", "ZEBRA"]

    def test_descending(self):
        chain = _make_chain(
            EnvVar("ZEBRA"), EnvVar("ALPHA"), EnvVar("MANGO")
        )
        result = sort_chain(chain, by="name", reverse=True)
        assert [v.name for v in result.vars] == ["ZEBRA", "MANGO", "ALPHA"]

    def test_preserves_profile(self):
        chain = _make_chain(EnvVar("A"), profile="staging")
        result = sort_chain(chain, by="name")
        assert result.profile == "staging"


class TestSortByValue:
    def test_set_values_before_unset(self, monkeypatch):
        monkeypatch.setenv("BRAVO", "hello")
        chain = _make_chain(EnvVar("ALPHA"), EnvVar("BRAVO"))
        result = sort_chain(chain, by="value")
        names = [v.name for v in result.vars]
        assert names.index("BRAVO") < names.index("ALPHA")

    def test_alphabetical_within_set(self, monkeypatch):
        monkeypatch.setenv("B_VAR", "z")
        monkeypatch.setenv("A_VAR", "a")
        chain = _make_chain(EnvVar("B_VAR"), EnvVar("A_VAR"))
        result = sort_chain(chain, by="value")
        assert [v.name for v in result.vars] == ["A_VAR", "B_VAR"]


class TestSortByHasDefault:
    def test_vars_with_default_come_first(self):
        chain = _make_chain(
            EnvVar("NO_DEFAULT"),
            EnvVar("HAS_DEFAULT", default="fallback"),
        )
        result = sort_chain(chain, by="has_default")
        assert result.vars[0].name == "HAS_DEFAULT"


class TestSortByIsSet:
    def test_set_vars_come_first(self, monkeypatch):
        monkeypatch.setenv("SET_VAR", "yes")
        chain = _make_chain(EnvVar("UNSET_VAR"), EnvVar("SET_VAR"))
        result = sort_chain(chain, by="is_set")
        assert result.vars[0].name == "SET_VAR"


class TestInvalidSortKey:
    def test_raises_value_error(self):
        chain = _make_chain(EnvVar("A"))
        with pytest.raises(ValueError, match="Unsupported sort key"):
            sort_chain(chain, by="nonexistent")

    def test_error_mentions_valid_keys(self):
        chain = _make_chain(EnvVar("A"))
        with pytest.raises(ValueError, match="name"):
            sort_chain(chain, by="bad")
