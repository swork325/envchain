"""Tests for envchain.cloner."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.cloner import CloneResult, clone_chain


def _make_chain(profile: str, **keys_defaults) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, default in keys_defaults.items():
        chain.add(EnvVar(key=key, default=default))
    return chain


class TestCloneResult:
    def test_repr_contains_profiles(self):
        r = CloneResult(source_profile="dev", target_profile="staging", cloned=["A"])
        assert "dev" in repr(r)
        assert "staging" in repr(r)

    def test_is_empty_when_nothing_cloned(self):
        r = CloneResult(source_profile="dev", target_profile="staging")
        assert r.is_empty is True

    def test_not_empty_when_cloned(self):
        r = CloneResult(source_profile="dev", target_profile="staging", cloned=["X"])
        assert r.is_empty is False


class TestCloneChain:
    def test_basic_clone_copies_all_vars(self):
        source = _make_chain("dev", DB_HOST="localhost", DB_PORT="5432")
        cloned, result = clone_chain(source, "staging")
        assert cloned.profile == "staging"
        assert set(v.key for v in cloned.vars) == {"DB_HOST", "DB_PORT"}
        assert result.cloned == ["DB_HOST", "DB_PORT"]
        assert result.skipped == []

    def test_clone_preserves_defaults(self):
        source = _make_chain("dev", API_URL="http://localhost")
        cloned, _ = clone_chain(source, "staging")
        var = next(v for v in cloned.vars if v.key == "API_URL")
        assert var.default == "http://localhost"

    def test_raises_for_unknown_target_profile(self):
        source = _make_chain("dev", FOO="bar")
        with pytest.raises(ValueError, match="Unknown target profile"):
            clone_chain(source, "unknown_env")

    def test_exclude_skips_specified_keys(self):
        source = _make_chain("dev", A="1", B="2", C="3")
        cloned, result = clone_chain(source, "staging", exclude=["B"])
        keys = {v.key for v in cloned.vars}
        assert "B" not in keys
        assert "B" in result.skipped
        assert "A" in result.cloned
        assert "C" in result.cloned

    def test_key_transform_applied(self):
        source = _make_chain("dev", db_host="localhost")
        cloned, result = clone_chain(
            source, "staging", key_transform=str.upper
        )
        keys = {v.key for v in cloned.vars}
        assert "DB_HOST" in keys
        assert result.cloned == ["db_host"]

    def test_source_profile_recorded_in_result(self):
        source = _make_chain("dev", X="1")
        _, result = clone_chain(source, "prod")
        assert result.source_profile == "dev"
        assert result.target_profile == "prod"

    def test_empty_source_produces_empty_clone(self):
        source = EnvChain(profile="dev")
        cloned, result = clone_chain(source, "staging")
        assert list(cloned.vars) == []
        assert result.is_empty

    def test_exclude_all_yields_empty_clone(self):
        source = _make_chain("dev", A="1", B="2")
        cloned, result = clone_chain(source, "staging", exclude=["A", "B"])
        assert result.is_empty
        assert len(result.skipped) == 2
