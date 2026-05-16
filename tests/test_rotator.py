"""Tests for envchain.rotator."""

from __future__ import annotations

import unittest

from envchain.chain import EnvChain, EnvVar
from envchain.rotator import RotationResult, rotate_chain


def _make_chain(*pairs: tuple[str, str | None], profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile=profile)
    for key, value in pairs:
        chain.add(EnvVar(key=key, value=value))
    return chain


class TestRotationResult(unittest.TestCase):
    def test_repr_contains_profile_and_counts(self):
        r = RotationResult(profile="dev", rotated={"A": "x"}, skipped=["B"])
        text = repr(r)
        self.assertIn("dev", text)
        self.assertIn("1", text)

    def test_is_empty_when_nothing_rotated(self):
        r = RotationResult(profile="dev")
        self.assertTrue(r.is_empty)

    def test_not_empty_when_rotated(self):
        r = RotationResult(profile="dev", rotated={"KEY": "new"})
        self.assertFalse(r.is_empty)


class TestRotateChain(unittest.TestCase):
    def _upper_gen(self, key: str, value):
        return value.upper() if value else None

    def test_all_keys_rotated_when_no_filter(self):
        chain = _make_chain(("A", "hello"), ("B", "world"))
        new_chain, result = rotate_chain(chain, self._upper_gen)
        self.assertEqual(result.rotated, {"A": "HELLO", "B": "WORLD"})
        self.assertEqual(result.skipped, [])

    def test_only_specified_keys_rotated(self):
        chain = _make_chain(("A", "hello"), ("B", "world"))
        new_chain, result = rotate_chain(chain, self._upper_gen, keys=["A"])
        self.assertIn("A", result.rotated)
        self.assertIn("B", result.skipped)

    def test_generator_returning_none_skips_key(self):
        chain = _make_chain(("A", "hello"), ("B", None))
        new_chain, result = rotate_chain(chain, self._upper_gen)
        self.assertIn("A", result.rotated)
        self.assertIn("B", result.skipped)

    def test_new_chain_has_updated_values(self):
        chain = _make_chain(("TOKEN", "abc"))
        new_chain, _ = rotate_chain(chain, lambda k, v: "xyz")
        var = next(v for v in new_chain.vars if v.key == "TOKEN")
        self.assertEqual(var.value, "xyz")

    def test_original_chain_unchanged(self):
        chain = _make_chain(("TOKEN", "abc"))
        rotate_chain(chain, lambda k, v: "xyz")
        var = next(v for v in chain.vars if v.key == "TOKEN")
        self.assertEqual(var.value, "abc")

    def test_profile_preserved_in_result(self):
        chain = _make_chain(("A", "v"), profile="prod")
        _, result = rotate_chain(chain, lambda k, v: "new")
        self.assertEqual(result.profile, "prod")

    def test_empty_chain_produces_empty_result(self):
        chain = EnvChain(profile="dev")
        new_chain, result = rotate_chain(chain, lambda k, v: "x")
        self.assertTrue(result.is_empty)
        self.assertEqual(list(new_chain.vars), [])

    def test_default_preserved_after_rotation(self):
        chain = EnvChain(profile="dev")
        chain.add(EnvVar(key="K", value="old", default="fallback"))
        new_chain, _ = rotate_chain(chain, lambda k, v: "new")
        var = next(v for v in new_chain.vars if v.key == "K")
        self.assertEqual(var.default, "fallback")
