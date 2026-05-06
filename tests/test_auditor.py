"""Unit tests for envchain.auditor."""

import pytest

from envchain.auditor import EnvAuditor
from envchain.chain import EnvChain
from envchain.validator import min_length, required, matches_prefix


def _chain_with(data: dict) -> EnvChain:
    """Build an EnvChain pre-populated with *data* (no env lookup needed)."""
    chain = EnvChain()
    for k, v in data.items():
        chain.add(k, default=v)
    return chain


class TestEnvAuditor:
    def test_passes_when_all_rules_satisfied(self):
        chain = _chain_with({"API_KEY": "sk-abc123"})
        auditor = EnvAuditor(chain)
        auditor.add_rule("API_KEY", required(), min_length(3))
        report = auditor.audit()
        assert report.passed is True

    def test_fails_when_required_value_missing(self):
        chain = _chain_with({})
        auditor = EnvAuditor(chain)
        auditor.add_rule("SECRET", required())
        report = auditor.audit()
        assert report.passed is False
        assert report.failures[0].key == "SECRET"

    def test_multiple_rules_combined_failure_message(self):
        chain = _chain_with({"TOKEN": "x"})
        auditor = EnvAuditor(chain)
        auditor.add_rule("TOKEN", min_length(10), matches_prefix("tok-"))
        report = auditor.audit()
        assert not report.passed
        assert ";" in report.failures[0].message

    def test_add_rule_returns_self_for_chaining(self):
        chain = _chain_with({})
        auditor = EnvAuditor(chain)
        result = auditor.add_rule("K", required())
        assert result is auditor

    def test_audit_or_raise_does_not_raise_on_success(self):
        chain = _chain_with({"DB_URL": "postgres://localhost/db"})
        auditor = EnvAuditor(chain)
        auditor.add_rule("DB_URL", required())
        auditor.audit_or_raise()  # should not raise

    def test_audit_or_raise_raises_on_failure(self):
        chain = _chain_with({})
        auditor = EnvAuditor(chain)
        auditor.add_rule("DB_URL", required())
        with pytest.raises(ValueError, match="EnvAuditor found issues"):
            auditor.audit_or_raise()

    def test_no_rules_produces_empty_report(self):
        chain = _chain_with({"FOO": "bar"})
        auditor = EnvAuditor(chain)
        report = auditor.audit()
        assert report.passed is True
        assert report.results == []
