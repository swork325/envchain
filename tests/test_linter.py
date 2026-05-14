"""Tests for envchain.linter."""

import pytest

from envchain.chain import EnvChain
from envchain.linter import LintReport, LintViolation, lint_chain


def _make_chain(profile: str = "dev", **defaults) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in defaults.items():
        chain.add(key, default=value)
    return chain


class TestLintViolation:
    def test_repr_contains_key_and_code(self):
        v = LintViolation("my_key", "E001", "Key should be uppercase")
        assert "my_key" in repr(v)
        assert "E001" in repr(v)


class TestLintReport:
    def test_passed_when_no_violations(self):
        report = LintReport(profile="dev")
        assert report.passed is True

    def test_failed_when_violations_present(self):
        report = LintReport(
            profile="dev",
            violations=[LintViolation("k", "E001", "msg")],
        )
        assert report.passed is False

    def test_repr_shows_pass(self):
        report = LintReport(profile="dev")
        assert "PASS" in repr(report)

    def test_repr_shows_violation_count(self):
        report = LintReport(
            profile="prod",
            violations=[
                LintViolation("a", "E001", "m"),
                LintViolation("b", "W001", "m"),
            ],
        )
        assert "2 violation" in repr(report)
        assert "prod" in repr(report)


class TestLintChain:
    def test_clean_chain_passes(self):
        chain = _make_chain("dev", DATABASE_URL="postgres://localhost/db")
        report = lint_chain(chain)
        assert report.passed

    def test_lowercase_key_triggers_e001(self):
        chain = _make_chain("dev", bad_key="value")
        report = lint_chain(chain)
        codes = [v.code for v in report.violations]
        assert "E001" in codes

    def test_blank_value_triggers_w001(self, monkeypatch):
        monkeypatch.setenv("BLANK_VAR", "   ")
        chain = EnvChain(profile="dev")
        chain.add("BLANK_VAR")
        report = lint_chain(chain)
        codes = [v.code for v in report.violations]
        assert "W001" in codes

    def test_placeholder_default_triggers_w002(self):
        chain = _make_chain("dev", SECRET_KEY="changeme")
        report = lint_chain(chain)
        codes = [v.code for v in report.violations]
        assert "W002" in codes

    def test_multiple_violations_on_same_key(self):
        chain = _make_chain("dev", lower_key="todo")
        report = lint_chain(chain)
        keys_with_violations = {v.key for v in report.violations}
        assert "lower_key" in keys_with_violations
        codes = [v.code for v in report.violations if v.key == "lower_key"]
        assert "E001" in codes
        assert "W002" in codes

    def test_report_profile_matches_chain(self):
        chain = _make_chain("staging", API_KEY="real-value")
        report = lint_chain(chain)
        assert report.profile == "staging"
