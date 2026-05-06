"""Tests for envchain.profiles module."""

import os
import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.profiles import EnvProfile, ProfileRegistry, KNOWN_PROFILES


class TestEnvProfile:
    def test_creates_profile_with_known_name(self):
        profile = EnvProfile("dev")
        assert profile.name == "dev"

    def test_creates_profile_with_all_known_names(self):
        for name in KNOWN_PROFILES:
            p = EnvProfile(name)
            assert p.name == name

    def test_raises_for_unknown_profile_name(self):
        with pytest.raises(ValueError, match="Unknown profile"):
            EnvProfile("local")

    def test_uses_provided_chain(self):
        chain = EnvChain()
        profile = EnvProfile("staging", chain=chain)
        assert profile.chain is chain

    def test_creates_default_chain_when_none_provided(self):
        profile = EnvProfile("prod")
        assert isinstance(profile.chain, EnvChain)


class TestProfileRegistry:
    def test_register_and_get_profile(self):
        registry = ProfileRegistry()
        profile = EnvProfile("dev")
        registry.register(profile)
        assert registry.get("dev") is profile

    def test_get_raises_for_unregistered_profile(self):
        registry = ProfileRegistry()
        with pytest.raises(KeyError, match="not registered"):
            registry.get("dev")

    def test_registered_names(self):
        registry = ProfileRegistry()
        registry.register(EnvProfile("dev"))
        registry.register(EnvProfile("prod"))
        assert set(registry.registered_names) == {"dev", "prod"}

    def test_active_returns_profile_based_on_env_var(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "staging")
        registry = ProfileRegistry()
        registry.register(EnvProfile("staging"))
        assert registry.active().name == "staging"

    def test_active_defaults_to_dev(self, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        registry = ProfileRegistry()
        registry.register(EnvProfile("dev"))
        assert registry.active().name == "dev"

    def test_validate_active_returns_true_when_valid(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.setenv("SECRET_KEY", "abc123")
        chain = EnvChain()
        chain.add(EnvVar("SECRET_KEY", required=True))
        registry = ProfileRegistry()
        registry.register(EnvProfile("prod", chain=chain))
        assert registry.validate_active() is True

    def test_validate_active_returns_false_when_invalid(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "prod")
        monkeypatch.delenv("MISSING_VAR", raising=False)
        chain = EnvChain()
        chain.add(EnvVar("MISSING_VAR", required=True))
        registry = ProfileRegistry()
        registry.register(EnvProfile("prod", chain=chain))
        assert registry.validate_active() is False
