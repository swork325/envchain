"""Tests for envchain.normalizer."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.normalizer import NormalizeResult, normalize_chain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chain(profile: str = "dev", **kwargs) -> EnvChain:
    """Build an EnvChain from keyword args {key: default}."""
    chain = EnvChain(profile=profile)
    for key, default in kwargs.items():
        chain.add(EnvVar(key=key, default=default))
    return chain


# ---------------------------------------------------------------------------
# NormalizeResult
# ---------------------------------------------------------------------------

class TestNormalizeResult:
    def test_is_clean_when_nothing_changed(self):
        chain = _make_chain(FOO="bar")
        result = normalize_chain(chain)
        assert result.is_clean

    def test_not_clean_when_keys_renamed(self):
        chain = _make_chain(foo="bar")
        result = normalize_chain(chain, uppercase_keys=True)
        assert not result.is_clean
        assert result.renamed_keys == [("foo", "FOO")]

    def test_not_clean_when_values_coerced(self):
        chain = _make_chain(FOO="  hello  ")
        result = normalize_chain(chain, strip_values=True)
        assert not result.is_clean
        assert "FOO" in result.coerced_values


# ---------------------------------------------------------------------------
# Key normalization
# ---------------------------------------------------------------------------

class TestKeyNormalization:
    def test_uppercase_keys_by_default(self):
        chain = _make_chain(database_url="postgres://localhost")
        result = normalize_chain(chain)
        keys = [v.key for v in result.normalized.vars]
        assert "DATABASE_URL" in keys
        assert "database_url" not in keys

    def test_uppercase_disabled(self):
        chain = _make_chain(database_url="postgres://localhost")
        result = normalize_chain(chain, uppercase_keys=False)
        keys = [v.key for v in result.normalized.vars]
        assert "database_url" in keys

    def test_spaces_in_keys_replaced(self):
        chain = EnvChain(profile="dev")
        chain.add(EnvVar(key="my key", default="val"))
        result = normalize_chain(chain, uppercase_keys=False)
        keys = [v.key for v in result.normalized.vars]
        assert "my_key" in keys

    def test_custom_space_replacement(self):
        chain = EnvChain(profile="dev")
        chain.add(EnvVar(key="my key", default="val"))
        result = normalize_chain(
            chain, uppercase_keys=False, space_replacement="-"
        )
        keys = [v.key for v in result.normalized.vars]
        assert "my-key" in keys

    def test_rename_recorded_once_per_key(self):
        chain = _make_chain(foo="1", bar="2")
        result = normalize_chain(chain)
        assert len(result.renamed_keys) == 2


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------

class TestValueNormalization:
    def test_strip_leading_trailing_whitespace(self):
        chain = _make_chain(FOO="  trimmed  ")
        result = normalize_chain(chain)
        normalized_var = result.normalized.vars[0]
        assert normalized_var.default == "trimmed"

    def test_none_default_not_coerced(self):
        chain = _make_chain(FOO=None)
        result = normalize_chain(chain)
        assert result.is_clean
        assert result.normalized.vars[0].default is None

    def test_strip_disabled(self):
        chain = _make_chain(FOO="  keep  ")
        result = normalize_chain(chain, strip_values=False)
        assert result.normalized.vars[0].default == "  keep  "

    def test_profile_preserved(self):
        chain = _make_chain(profile="staging", FOO="bar")
        result = normalize_chain(chain)
        assert result.normalized.profile == "staging"
        assert result.profile == "staging"
