"""Tests for envchain.freezer."""

import json
import pytest

from envchain.chain import EnvChain, EnvVar
from envchain.freezer import FrozenChain, freeze, thaw, diff_frozen


def _make_chain(*pairs) -> EnvChain:
    chain = EnvChain()
    for key, default in pairs:
        chain.add(EnvVar(key=key, default=default))
    return chain


class TestFrozenChain:
    def test_to_dict_round_trip(self):
        fc = FrozenChain(profile="prod", values={"A": "1", "B": None})
        assert FrozenChain.from_dict(fc.to_dict()) == fc

    def test_to_json_round_trip(self):
        fc = FrozenChain(profile="staging", values={"X": "hello"})
        assert FrozenChain.from_json(fc.to_json()) == fc

    def test_json_is_valid_json(self):
        fc = FrozenChain(profile="dev", values={"K": "v"})
        parsed = json.loads(fc.to_json())
        assert parsed["profile"] == "dev"
        assert parsed["values"] == {"K": "v"}

    def test_equality(self):
        a = FrozenChain(profile="dev", values={"K": "v"})
        b = FrozenChain(profile="dev", values={"K": "v"})
        assert a == b

    def test_inequality_different_profile(self):
        a = FrozenChain(profile="dev", values={"K": "v"})
        b = FrozenChain(profile="prod", values={"K": "v"})
        assert a != b


class TestFreeze:
    def test_captures_default_values(self):
        chain = _make_chain(("HOST", "localhost"), ("PORT", "5432"))
        fc = freeze(chain, profile="dev")
        assert fc.values["HOST"] == "localhost"
        assert fc.values["PORT"] == "5432"

    def test_profile_stored(self):
        chain = _make_chain(("A", "1"))
        fc = freeze(chain, profile="staging")
        assert fc.profile == "staging"

    def test_none_value_for_missing_env_var(self, monkeypatch):
        monkeypatch.delenv("UNDEFINED_KEY_XYZ", raising=False)
        chain = _make_chain(("UNDEFINED_KEY_XYZ", None))
        fc = freeze(chain)
        assert fc.values["UNDEFINED_KEY_XYZ"] is None


class TestThaw:
    def test_thaw_restores_keys(self):
        fc = FrozenChain(profile="dev", values={"A": "1", "B": "2"})
        chain = thaw(fc)
        keys = [v.key for v in chain._vars]
        assert "A" in keys and "B" in keys

    def test_thaw_resolves_values_as_defaults(self):
        fc = FrozenChain(profile="dev", values={"DB": "postgres"})
        chain = thaw(fc)
        var = next(v for v in chain._vars if v.key == "DB")
        assert var.resolve() == "postgres"

    def test_freeze_thaw_round_trip(self):
        original = _make_chain(("FOO", "bar"), ("BAZ", "qux"))
        fc = freeze(original, profile="test")
        restored = thaw(fc)
        for var in original._vars:
            restored_var = next(v for v in restored._vars if v.key == var.key)
            assert restored_var.resolve() == var.resolve()


class TestDiffFrozen:
    def test_no_diff_for_identical_frozen_chains(self):
        fc = FrozenChain(profile="dev", values={"A": "1"})
        entries = diff_frozen(fc, fc)
        assert entries == []

    def test_detects_added_key(self):
        before = FrozenChain(profile="dev", values={"A": "1"})
        after = FrozenChain(profile="dev", values={"A": "1", "B": "2"})
        entries = diff_frozen(before, after)
        keys = [e.key for e in entries]
        assert "B" in keys

    def test_detects_value_change(self):
        before = FrozenChain(profile="dev", values={"A": "old"})
        after = FrozenChain(profile="dev", values={"A": "new"})
        entries = diff_frozen(before, after)
        assert len(entries) == 1
        assert entries[0].key == "A"
        assert entries[0].is_value_diff()
