"""Tests for envchain.labeler."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.labeler import LabeledVar, LabelReport, label_chain


def _make_chain(*keys: str, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key in keys:
        chain.add(EnvVar(key=key, default=f"val_{key}"))
    return chain


class TestLabeledVar:
    def test_get_returns_label_value(self):
        var = EnvVar(key="DB_URL", default="sqlite")
        lv = LabeledVar(var=var, labels={"tier": "database"})
        assert lv.get("tier") == "database"

    def test_get_returns_none_for_missing_label(self):
        var = EnvVar(key="DB_URL", default="sqlite")
        lv = LabeledVar(var=var, labels={})
        assert lv.get("tier") is None

    def test_has_label_true(self):
        var = EnvVar(key="API_KEY", default="abc")
        lv = LabeledVar(var=var, labels={"secret": "true"})
        assert lv.has_label("secret") is True

    def test_has_label_false(self):
        var = EnvVar(key="API_KEY", default="abc")
        lv = LabeledVar(var=var, labels={})
        assert lv.has_label("secret") is False


class TestLabelReport:
    def _report(self) -> LabelReport:
        chain = _make_chain("DB_URL", "API_KEY", "LOG_LEVEL")
        rules = {
            "DB_URL": {"tier": "database", "sensitive": "false"},
            "API_KEY": {"tier": "auth", "sensitive": "true"},
        }
        return label_chain(chain, rules)

    def test_profile_stored(self):
        report = self._report()
        assert report.profile == "dev"

    def test_entry_count_matches_chain(self):
        report = self._report()
        assert len(report.entries) == 3

    def test_unlabeled_var_has_empty_labels(self):
        report = self._report()
        log_entry = next(e for e in report.entries if e.var.key == "LOG_LEVEL")
        assert log_entry.labels == {}

    def test_where_filters_by_label_value(self):
        report = self._report()
        db_entries = report.where("tier", "database")
        assert len(db_entries) == 1
        assert db_entries[0].var.key == "DB_URL"

    def test_where_returns_empty_when_no_match(self):
        report = self._report()
        assert report.where("tier", "nonexistent") == []

    def test_keys_with_returns_keys_carrying_label(self):
        report = self._report()
        keys = report.keys_with("sensitive")
        assert set(keys) == {"DB_URL", "API_KEY"}

    def test_keys_with_returns_empty_for_absent_label(self):
        report = self._report()
        assert report.keys_with("unknown") == []


class TestLabelChain:
    def test_empty_rules_produces_empty_labels(self):
        chain = _make_chain("A", "B")
        report = label_chain(chain, {})
        for entry in report.entries:
            assert entry.labels == {}

    def test_partial_rules_applied_correctly(self):
        chain = _make_chain("X", "Y")
        report = label_chain(chain, {"X": {"env": "prod"}})
        x_entry = next(e for e in report.entries if e.var.key == "X")
        y_entry = next(e for e in report.entries if e.var.key == "Y")
        assert x_entry.get("env") == "prod"
        assert y_entry.get("env") is None

    def test_multiple_labels_on_single_var(self):
        chain = _make_chain("SECRET")
        report = label_chain(chain, {"SECRET": {"tier": "auth", "rotate": "90d"}})
        entry = report.entries[0]
        assert entry.get("tier") == "auth"
        assert entry.get("rotate") == "90d"
