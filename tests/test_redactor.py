"""Tests for envchain.redactor."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.redactor import (
    REDACTED_PLACEHOLDER,
    RedactedVar,
    RedactReport,
    redact_chain,
)


def _make_chain(*pairs, profile="dev"):
    chain = EnvChain(profile=profile)
    for key, value in pairs:
        chain.add(EnvVar(key=key, default=value))
    return chain


class TestRedactedVar:
    def test_plain_var_display_value(self):
        v = RedactedVar(key="HOST", original="localhost", redacted=False)
        assert v.display_value == "localhost"

    def test_redacted_var_display_value(self):
        v = RedactedVar(key="API_KEY", original="secret123", redacted=True)
        assert v.display_value == REDACTED_PLACEHOLDER

    def test_redacted_var_with_none_original(self):
        v = RedactedVar(key="TOKEN", original=None, redacted=True)
        assert v.display_value == REDACTED_PLACEHOLDER

    def test_plain_var_with_none_original(self):
        v = RedactedVar(key="OPTIONAL", original=None, redacted=False)
        assert v.display_value is None


class TestRedactReport:
    def test_redacted_keys_list(self):
        report = RedactReport(
            profile="prod",
            vars=[
                RedactedVar("DB_PASSWORD", "s3cr3t", True),
                RedactedVar("HOST", "db.local", False),
            ],
        )
        assert report.redacted_keys == ["DB_PASSWORD"]

    def test_plain_keys_list(self):
        report = RedactReport(
            profile="prod",
            vars=[
                RedactedVar("DB_PASSWORD", "s3cr3t", True),
                RedactedVar("HOST", "db.local", False),
            ],
        )
        assert report.plain_keys == ["HOST"]

    def test_empty_report(self):
        report = RedactReport(profile="dev")
        assert report.redacted_keys == []
        assert report.plain_keys == []


class TestRedactChain:
    def test_sensitive_keys_are_redacted(self):
        chain = _make_chain(
            ("DB_PASSWORD", "hunter2"),
            ("API_KEY", "abc123"),
            ("SECRET_TOKEN", "xyz"),
        )
        report = redact_chain(chain)
        assert set(report.redacted_keys) == {"DB_PASSWORD", "API_KEY", "SECRET_TOKEN"}

    def test_plain_keys_are_not_redacted(self):
        chain = _make_chain(("HOST", "localhost"), ("PORT", "5432"))
        report = redact_chain(chain)
        assert report.redacted_keys == []
        assert set(report.plain_keys) == {"HOST", "PORT"}

    def test_mixed_chain(self):
        chain = _make_chain(
            ("APP_NAME", "myapp"),
            ("AUTH_TOKEN", "tok-secret"),
            ("LOG_LEVEL", "info"),
        )
        report = redact_chain(chain)
        assert "AUTH_TOKEN" in report.redacted_keys
        assert "APP_NAME" in report.plain_keys
        assert "LOG_LEVEL" in report.plain_keys

    def test_custom_patterns_override_defaults(self):
        chain = _make_chain(("DB_PASSWORD", "s3cr3t"), ("CUSTOM_SENSITIVE", "val"))
        report = redact_chain(chain, patterns=[r"(?i)custom"])
        assert report.redacted_keys == ["CUSTOM_SENSITIVE"]
        assert "DB_PASSWORD" in report.plain_keys

    def test_profile_preserved_in_report(self):
        chain = _make_chain(("X", "1"), profile="staging")
        report = redact_chain(chain)
        assert report.profile == "staging"

    def test_none_value_var_handled(self):
        chain = _make_chain(("SECRET", None))
        report = redact_chain(chain)
        assert report.redacted_keys == ["SECRET"]
        assert report.vars[0].display_value == REDACTED_PLACEHOLDER
