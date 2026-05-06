"""Unit tests for envchain.validator."""

import pytest

from envchain.validator import (
    ValidationReport,
    ValidationResult,
    matches_prefix,
    min_length,
    required,
)


class TestValidationResult:
    def test_passed_repr(self):
        r = ValidationResult(key="FOO", passed=True)
        assert "OK" in repr(r)

    def test_failed_repr_includes_message(self):
        r = ValidationResult(key="FOO", passed=False, message="oops")
        assert "FAIL" in repr(r)
        assert "oops" in repr(r)


class TestValidationReport:
    def test_passes_when_all_results_pass(self):
        report = ValidationReport(
            results=[ValidationResult("A", True), ValidationResult("B", True)]
        )
        assert report.passed is True

    def test_fails_when_any_result_fails(self):
        report = ValidationReport(
            results=[ValidationResult("A", True), ValidationResult("B", False, "bad")]
        )
        assert report.passed is False
        assert len(report.failures) == 1

    def test_summary_all_pass(self):
        report = ValidationReport(results=[ValidationResult("X", True)])
        assert "passed" in report.summary()

    def test_summary_failures(self):
        report = ValidationReport(
            results=[ValidationResult("X", False, "missing")]
        )
        assert "failed" in report.summary()
        assert "missing" in report.summary()


class TestRules:
    def test_required_passes_for_value(self):
        assert required()("hello") is None

    def test_required_fails_for_none(self):
        assert required()(None) is not None

    def test_required_fails_for_empty_string(self):
        assert required()("") is not None

    def test_min_length_passes(self):
        assert min_length(3)("abc") is None

    def test_min_length_fails(self):
        assert min_length(5)("hi") is not None

    def test_min_length_ignores_none(self):
        assert min_length(3)(None) is None

    def test_matches_prefix_passes(self):
        assert matches_prefix("sk-")("sk-abc123") is None

    def test_matches_prefix_fails(self):
        assert matches_prefix("sk-")("pk-abc123") is not None

    def test_matches_prefix_ignores_none(self):
        assert matches_prefix("sk-")(None) is None
