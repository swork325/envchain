"""Integration tests for aliaser + exporter pipeline."""

from __future__ import annotations

import json

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.aliaser import alias_chain
from envchain.exporter import export_chain


def _make_chain(*items: tuple, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in items:
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestAliasExporterIntegration:
    def test_alias_report_keys_match_chain_keys(self):
        chain = _make_chain(("DB_HOST", "localhost"), ("DB_PORT", "5432"))
        report = alias_chain(chain, {"DB_HOST": "host", "DB_PORT": "port"})
        chain_keys = {v.key for v in chain.vars}
        report_keys = {e.var.key for e in report.entries}
        assert chain_keys == report_keys

    def test_exported_dotenv_contains_aliased_keys(self):
        chain = _make_chain(
            ("DB_HOST", "localhost"),
            ("API_KEY", "abc123"),
        )
        report = alias_chain(chain, {"DB_HOST": "database_host"})
        dotenv_output = export_chain(chain, fmt="dotenv")
        # Original keys are exported; aliases are metadata only
        assert "DB_HOST" in dotenv_output
        assert "API_KEY" in dotenv_output
        # Alias display keys are separate from export
        assert report.by_alias("database_host") is not None

    def test_unaliased_vars_have_none_alias(self):
        chain = _make_chain(("SECRET", "topsecret"), ("TOKEN", "abc"))
        report = alias_chain(chain, {"SECRET": "the_secret"})
        token_entry = next(e for e in report.entries if e.var.key == "TOKEN")
        assert token_entry.alias is None
        assert token_entry.display_key == "TOKEN"

    def test_json_export_and_alias_report_share_same_keys(self):
        chain = _make_chain(("HOST", "127.0.0.1"), ("PORT", "8080"))
        report = alias_chain(chain, {"HOST": "hostname"})
        json_output = export_chain(chain, fmt="json")
        exported = json.loads(json_output)
        exported_keys = set(exported.keys())
        report_keys = {e.var.key for e in report.entries}
        assert exported_keys == report_keys
