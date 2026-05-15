"""Tests for envchain.promoter."""

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.promoter import PromotionResult, next_profile, promote_chain


def _make_chain(profile: str, **kv: str) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kv.items():
        chain.add(EnvVar(key=key, default=value))
    return chain


# ---------------------------------------------------------------------------
# next_profile
# ---------------------------------------------------------------------------

class TestNextProfile:
    def test_dev_promotes_to_staging(self):
        assert next_profile("dev") == "staging"

    def test_staging_promotes_to_prod(self):
        assert next_profile("staging") == "prod"

    def test_prod_returns_none(self):
        assert next_profile("prod") is None

    def test_unknown_profile_raises(self):
        with pytest.raises(ValueError, match="Unknown profile"):
            next_profile("canary")


# ---------------------------------------------------------------------------
# PromotionResult
# ---------------------------------------------------------------------------

class TestPromotionResult:
    def test_is_empty_when_no_promoted_keys(self):
        r = PromotionResult(source_profile="dev", target_profile="staging", promoted_keys=[])
        assert r.is_empty

    def test_not_empty_when_promoted_keys_present(self):
        r = PromotionResult(
            source_profile="dev", target_profile="staging", promoted_keys=["FOO"]
        )
        assert not r.is_empty


# ---------------------------------------------------------------------------
# promote_chain
# ---------------------------------------------------------------------------

class TestPromoteChain:
    def test_promotes_all_keys_by_default(self):
        src = _make_chain("dev", FOO="foo_val", BAR="bar_val")
        tgt = _make_chain("staging")
        new_chain, result = promote_chain(src, tgt)
        assert set(result.promoted_keys) == {"FOO", "BAR"}
        assert result.skipped_keys == []

    def test_target_profile_preserved(self):
        src = _make_chain("dev", FOO="val")
        tgt = _make_chain("staging")
        new_chain, _ = promote_chain(src, tgt)
        assert new_chain.profile == "staging"

    def test_existing_key_not_overwritten_by_default(self):
        src = _make_chain("dev", FOO="new_val")
        tgt = _make_chain("staging", FOO="old_val")
        new_chain, result = promote_chain(src, tgt)
        assert "FOO" in result.skipped_keys
        resolved = {v.key: v.resolve() for v in new_chain.vars}
        assert resolved["FOO"] == "old_val"

    def test_existing_key_overwritten_when_flag_set(self):
        src = _make_chain("dev", FOO="new_val")
        tgt = _make_chain("staging", FOO="old_val")
        new_chain, result = promote_chain(src, tgt, overwrite=True)
        assert "FOO" in result.promoted_keys
        resolved = {v.key: v.resolve() for v in new_chain.vars}
        assert resolved["FOO"] == "new_val"

    def test_explicit_keys_subset_promoted(self):
        src = _make_chain("dev", FOO="f", BAR="b", BAZ="z")
        tgt = _make_chain("staging")
        new_chain, result = promote_chain(src, tgt, keys=["FOO", "BAZ"])
        assert set(result.promoted_keys) == {"FOO", "BAZ"}
        assert "BAR" not in result.promoted_keys

    def test_missing_key_in_source_is_skipped(self):
        src = _make_chain("dev", FOO="val")
        tgt = _make_chain("staging")
        _, result = promote_chain(src, tgt, keys=["FOO", "MISSING"])
        assert "MISSING" in result.skipped_keys

    def test_source_var_with_no_resolved_value_is_skipped(self):
        src = EnvChain(profile="dev")
        src.add(EnvVar(key="EMPTY"))  # no default, not in env
        tgt = _make_chain("staging")
        _, result = promote_chain(src, tgt)
        assert "EMPTY" in result.skipped_keys

    def test_target_retains_non_promoted_keys(self):
        src = _make_chain("dev", FOO="foo")
        tgt = _make_chain("staging", KEEP="keep_val")
        new_chain, _ = promote_chain(src, tgt)
        keys = [v.key for v in new_chain.vars]
        assert "KEEP" in keys
