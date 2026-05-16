"""Tests for envchain.inspector."""

import os
import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.inspector import InspectEntry, InspectReport, inspect_chain


def _make_chain(profile: str = "dev", **vars_: EnvVar) -> EnvChain:
    chain = EnvChain(profile=profile)
    for var in vars_.values():
        chain.add(var)
    return chain


class TestInspectEntry:
    def test_repr_contains_key_and_source(self):
        entry = InspectEntry(
            key="FOO",
            value="bar",
            default=None,
            has_value=True,
            has_default=False,
            is_empty=False,
            source="env",
        )
        r = repr(entry)
        assert "FOO" in r
        assert "env" in r


class TestInspectReport:
    def _report(self, monkeypatch) -> InspectReport:
        monkeypatch.setenv("APP_HOST", "localhost")
        monkeypatch.delenv("APP_SECRET", raising=False)
        chain = EnvChain(profile="staging")
        chain.add(EnvVar("APP_HOST"))
        chain.add(EnvVar("APP_PORT", default="8080"))
        chain.add(EnvVar("APP_SECRET"))
        return inspect_chain(chain)

    def test_profile_stored(self, monkeypatch):
        report = self._report(monkeypatch)
        assert report.profile == "staging"

    def test_total_entries_match_chain(self, monkeypatch):
        report = self._report(monkeypatch)
        assert len(report.entries) == 3

    def test_get_returns_entry_by_key(self, monkeypatch):
        report = self._report(monkeypatch)
        entry = report.get("APP_HOST")
        assert entry is not None
        assert entry.key == "APP_HOST"

    def test_get_returns_none_for_unknown_key(self, monkeypatch):
        report = self._report(monkeypatch)
        assert report.get("DOES_NOT_EXIST") is None

    def test_missing_identifies_unset_no_default(self, monkeypatch):
        report = self._report(monkeypatch)
        missing_keys = [e.key for e in report.missing]
        assert "APP_SECRET" in missing_keys
        assert "APP_HOST" not in missing_keys

    def test_sourced_from_default_when_env_absent(self, monkeypatch):
        report = self._report(monkeypatch)
        default_keys = [e.key for e in report.sourced_from_default]
        assert "APP_PORT" in default_keys

    def test_env_source_when_value_set(self, monkeypatch):
        report = self._report(monkeypatch)
        entry = report.get("APP_HOST")
        assert entry is not None
        assert entry.source == "env"
        assert entry.has_value is True

    def test_is_empty_flag_for_blank_value(self, monkeypatch):
        monkeypatch.setenv("BLANK_VAR", "")
        chain = EnvChain(profile="dev")
        chain.add(EnvVar("BLANK_VAR"))
        report = inspect_chain(chain)
        entry = report.get("BLANK_VAR")
        assert entry is not None
        assert entry.is_empty is True

    def test_has_default_flag(self, monkeypatch):
        report = self._report(monkeypatch)
        entry = report.get("APP_PORT")
        assert entry is not None
        assert entry.has_default is True

    def test_missing_entry_has_no_value(self, monkeypatch):
        report = self._report(monkeypatch)
        entry = report.get("APP_SECRET")
        assert entry is not None
        assert entry.has_value is False
        assert entry.value is None
