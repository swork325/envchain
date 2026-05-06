"""Tests for the EnvChain core module."""

import os
import pytest
from envchain.chain import EnvVar, EnvChain


class TestEnvVar:
    def test_resolves_from_environment(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "hello")
        var = EnvVar(name="MY_VAR")
        assert var.resolve() == "hello"

    def test_returns_default_when_missing(self):
        var = EnvVar(name="MISSING_VAR_XYZ", default="fallback")
        assert var.resolve() == "fallback"

    def test_returns_none_when_missing_and_no_default(self):
        var = EnvVar(name="MISSING_VAR_XYZ")
        assert var.resolve() is None


class TestEnvChain:
    def test_add_returns_self_for_chaining(self):
        chain = EnvChain(name="test")
        result = chain.add("VAR_ONE").add("VAR_TWO")
        assert result is chain
        assert len(chain.variables) == 2

    def test_validate_reports_missing_required(self):
        chain = EnvChain(name="prod")
        chain.add("DEFINITELY_NOT_SET_ABC123", required=True)
        result = chain.validate()
        assert "DEFINITELY_NOT_SET_ABC123" in result["missing"]

    def test_validate_reports_resolved(self, monkeypatch):
        monkeypatch.setenv("APP_SECRET", "s3cr3t")
        chain = EnvChain(name="prod")
        chain.add("APP_SECRET", required=True)
        result = chain.validate()
        assert "APP_SECRET" in result["resolved"]
        assert result["missing"] == []

    def test_optional_var_not_in_missing(self):
        chain = EnvChain(name="dev")
        chain.add("OPTIONAL_VAR_XYZ", required=False)
        result = chain.validate()
        assert "OPTIONAL_VAR_XYZ" not in result["missing"]

    def test_is_valid_true_when_all_present(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        chain = EnvChain(name="staging")
        chain.add("DB_HOST")
        assert chain.is_valid() is True

    def test_is_valid_false_when_missing(self):
        chain = EnvChain(name="prod")
        chain.add("MISSING_REQUIRED_XYZ123")
        assert chain.is_valid() is False

    def test_as_dict_returns_all_values(self, monkeypatch):
        monkeypatch.setenv("PORT", "8080")
        chain = EnvChain(name="dev")
        chain.add("PORT").add("TIMEOUT", required=False, default="30")
        result = chain.as_dict()
        assert result["PORT"] == "8080"
        assert result["TIMEOUT"] == "30"
