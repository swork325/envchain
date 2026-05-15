"""Tests for envchain.summarizer."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.summarizer import SummaryReport, summarize_chain


def _make_chain(profile: str = "test", **vars_) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, (env_key, default) in vars_.items():
        chain.add(EnvVar(key=key, env_key=env_key, default=default))
    return chain


class TestSummaryReport:
    def test_repr_contains_profile_and_counts(self):
        report = SummaryReport(
            profile="prod", total=3, resolved=1, defaulted=1, missing=1
        )
        r = repr(report)
        assert "prod" in r
        assert "total=3" in r
        assert "missing=1" in r

    def test_to_dict_has_all_keys(self):
        report = SummaryReport(
            profile="dev",
            total=2,
            resolved=2,
            defaulted=0,
            missing=0,
            keys=["A", "B"],
            missing_keys=[],
        )
        d = report.to_dict()
        assert d["profile"] == "dev"
        assert d["total"] == 2
        assert d["resolved"] == 2
        assert d["defaulted"] == 0
        assert d["missing"] == 0
        assert d["keys"] == ["A", "B"]
        assert d["missing_keys"] == []


class TestSummarizeChain:
    def test_empty_chain(self):
        chain = EnvChain(profile="dev")
        report = summarize_chain(chain)
        assert report.total == 0
        assert report.resolved == 0
        assert report.missing == 0
        assert report.defaulted == 0

    def test_counts_missing_when_no_env_and_no_default(self, monkeypatch):
        monkeypatch.delenv("MY_SECRET", raising=False)
        chain = _make_chain(MY_SECRET=("MY_SECRET", None))
        report = summarize_chain(chain)
        assert report.missing == 1
        assert "MY_SECRET" in report.missing_keys

    def test_counts_defaulted_when_env_missing_but_default_set(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        chain = _make_chain(APP_ENV=("APP_ENV", "development"))
        report = summarize_chain(chain)
        assert report.defaulted == 1
        assert report.missing == 0

    def test_counts_resolved_when_env_present(self, monkeypatch):
        monkeypatch.setenv("DB_URL", "postgres://localhost/db")
        chain = _make_chain(DB_URL=("DB_URL", None))
        report = summarize_chain(chain)
        assert report.resolved == 1
        assert report.missing == 0

    def test_total_is_sum_of_all(self, monkeypatch):
        monkeypatch.setenv("PRESENT", "yes")
        monkeypatch.delenv("ABSENT", raising=False)
        monkeypatch.delenv("DEFAULTED", raising=False)
        chain = _make_chain(
            PRESENT=("PRESENT", None),
            ABSENT=("ABSENT", None),
            DEFAULTED=("DEFAULTED", "fallback"),
        )
        report = summarize_chain(chain)
        assert report.total == 3

    def test_profile_stored_correctly(self):
        chain = EnvChain(profile="staging")
        report = summarize_chain(chain)
        assert report.profile == "staging"

    def test_keys_are_sorted(self, monkeypatch):
        monkeypatch.setenv("Z_VAR", "1")
        monkeypatch.setenv("A_VAR", "2")
        chain = _make_chain(Z_VAR=("Z_VAR", None), A_VAR=("A_VAR", None))
        report = summarize_chain(chain)
        assert report.keys == sorted(report.keys)
