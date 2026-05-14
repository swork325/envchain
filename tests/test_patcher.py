"""Tests for envchain.patcher."""

from __future__ import annotations

import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.patcher import PatchResult, patch_chain


def _make_chain(profile: str = "dev", **kv: str) -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in kv.items():
        chain.add(EnvVar(key=key, value=value))
    return chain


class TestPatchResult:
    def test_is_empty_when_no_changes(self):
        pr = PatchResult()
        assert pr.is_empty is True

    def test_not_empty_when_added(self):
        pr = PatchResult(added=["FOO"])
        assert pr.is_empty is False

    def test_not_empty_when_updated(self):
        pr = PatchResult(updated=["BAR"])
        assert pr.is_empty is False

    def test_not_empty_when_removed(self):
        pr = PatchResult(removed=["BAZ"])
        assert pr.is_empty is False


class TestPatchChain:
    def test_no_changes_returns_same_keys(self):
        chain = _make_chain(FOO="bar")
        patched, result = patch_chain(chain)
        keys = [v.key for v in patched._vars]
        assert keys == ["FOO"]
        assert result.is_empty

    def test_override_existing_key(self):
        chain = _make_chain(FOO="old")
        patched, result = patch_chain(chain, overrides={"FOO": "new"})
        resolved = {v.key: v.value for v in patched._vars}
        assert resolved["FOO"] == "new"
        assert result.updated == ["FOO"]
        assert result.added == []

    def test_add_new_key_via_overrides(self):
        chain = _make_chain(FOO="bar")
        patched, result = patch_chain(chain, overrides={"EXTRA": "value"})
        keys = [v.key for v in patched._vars]
        assert "EXTRA" in keys
        assert result.added == ["EXTRA"]

    def test_remove_existing_key(self):
        chain = _make_chain(FOO="bar", BAZ="qux")
        patched, result = patch_chain(chain, removals=["FOO"])
        keys = [v.key for v in patched._vars]
        assert "FOO" not in keys
        assert "BAZ" in keys
        assert result.removed == ["FOO"]

    def test_removal_takes_precedence_over_override(self):
        chain = _make_chain(FOO="bar")
        patched, result = patch_chain(
            chain, overrides={"FOO": "new"}, removals=["FOO"]
        )
        keys = [v.key for v in patched._vars]
        assert "FOO" not in keys
        assert result.removed == ["FOO"]
        assert result.updated == []

    def test_profile_preserved(self):
        chain = _make_chain(profile="staging", FOO="1")
        patched, _ = patch_chain(chain, overrides={"BAR": "2"})
        assert patched.profile == "staging"

    def test_override_with_none_clears_value(self):
        chain = _make_chain(FOO="something")
        patched, result = patch_chain(chain, overrides={"FOO": None})
        resolved = {v.key: v.value for v in patched._vars}
        assert resolved["FOO"] is None
        assert "FOO" in result.updated
