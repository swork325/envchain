"""Tests for envchain.aliaser."""

from __future__ import annotations

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.aliaser import AliasedVar, AliasReport, alias_chain


def _make_chain(*keys: str, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key in keys:
        chain.add(EnvVar(key=key, default=f"val_{key}"))
    return chain


class TestAliasedVar:
    def test_display_key_returns_alias_when_set(self):
        var = EnvVar(key="DB_HOST", default="localhost")
        av = AliasedVar(var=var, alias="database_host")
        assert av.display_key == "database_host"

    def test_display_key_returns_key_when_no_alias(self):
        var = EnvVar(key="DB_HOST", default="localhost")
        av = AliasedVar(var=var)
        assert av.display_key == "DB_HOST"

    def test_alias_none_by_default(self):
        var = EnvVar(key="API_KEY", default=None)
        av = AliasedVar(var=var)
        assert av.alias is None


class TestAliasReport:
    def test_aliased_keys_returns_only_mapped_keys(self):
        chain = _make_chain("DB_HOST", "API_KEY", "SECRET")
        report = alias_chain(chain, {"DB_HOST": "database_host", "SECRET": "secret_key"})
        assert set(report.aliased_keys) == {"DB_HOST", "SECRET"}

    def test_aliased_keys_empty_when_no_aliases(self):
        chain = _make_chain("DB_HOST", "API_KEY")
        report = alias_chain(chain, {})
        assert report.aliased_keys == []

    def test_by_alias_returns_correct_entry(self):
        chain = _make_chain("DB_HOST", "API_KEY")
        report = alias_chain(chain, {"DB_HOST": "database_host"})
        entry = report.by_alias("database_host")
        assert entry is not None
        assert entry.var.key == "DB_HOST"

    def test_by_alias_returns_none_for_unknown(self):
        chain = _make_chain("DB_HOST")
        report = alias_chain(chain, {"DB_HOST": "database_host"})
        assert report.by_alias("nonexistent") is None

    def test_profile_preserved(self):
        chain = _make_chain("KEY", profile="staging")
        report = alias_chain(chain, {})
        assert report.profile == "staging"


class TestAliasChain:
    def test_all_vars_included(self):
        chain = _make_chain("A", "B", "C")
        report = alias_chain(chain, {})
        assert len(report.entries) == 3

    def test_partial_alias_map(self):
        chain = _make_chain("DB_HOST", "DB_PORT", "API_KEY")
        report = alias_chain(chain, {"DB_HOST": "host"})
        aliased = {e.var.key: e.alias for e in report.entries}
        assert aliased["DB_HOST"] == "host"
        assert aliased["DB_PORT"] is None
        assert aliased["API_KEY"] is None

    def test_full_alias_map(self):
        chain = _make_chain("X", "Y")
        report = alias_chain(chain, {"X": "ex", "Y": "why"})
        assert len(report.aliased_keys) == 2

    def test_empty_chain_produces_empty_report(self):
        chain = EnvChain(profile="dev")
        report = alias_chain(chain, {"MISSING": "alias"})
        assert report.entries == []
        assert report.aliased_keys == []
