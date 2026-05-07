"""Tests for envchain.transformer module."""

import pytest
from envchain.chain import EnvChain, EnvVar
from envchain.transformer import (
    strip_whitespace,
    to_uppercase,
    to_lowercase,
    mask_value,
    prefix,
    apply_transforms,
    transform_key,
)


def _make_chain(pairs: dict, profile: str = "dev") -> EnvChain:
    chain = EnvChain(profile)
    for key, val in pairs.items():
        var = EnvVar(key, default=val)
        chain._vars.append(var)
    return chain


class TestBuiltinTransforms:
    def test_strip_whitespace_removes_spaces(self):
        assert strip_whitespace("  hello  ") == "hello"

    def test_strip_whitespace_none_passthrough(self):
        assert strip_whitespace(None) is None

    def test_to_uppercase(self):
        assert to_uppercase("hello") == "HELLO"

    def test_to_uppercase_none_passthrough(self):
        assert to_uppercase(None) is None

    def test_to_lowercase(self):
        assert to_lowercase("HELLO") == "hello"

    def test_to_lowercase_none_passthrough(self):
        assert to_lowercase(None) is None


class TestMaskTransform:
    def test_masks_all_but_last_four(self):
        fn = mask_value()
        assert fn("mysecrettoken") == "*********oken"

    def test_masks_short_value_entirely(self):
        fn = mask_value()
        assert fn("abc") == "***"

    def test_custom_visible_chars(self):
        fn = mask_value(visible=2)
        assert fn("abcdef") == "****ef"

    def test_none_passthrough(self):
        fn = mask_value()
        assert fn(None) is None


class TestPrefixTransform:
    def test_prepends_text(self):
        fn = prefix("Bearer ")
        assert fn("token123") == "Bearer token123"

    def test_none_passthrough(self):
        fn = prefix("Bearer ")
        assert fn(None) is None


class TestApplyTransforms:
    def test_transforms_all_values(self):
        chain = _make_chain({"HOST": "  localhost  ", "ENV": "  dev  "})
        result = apply_transforms(chain, [strip_whitespace])
        values = {v.key: v.resolve() for v in result._vars}
        assert values["HOST"] == "localhost"
        assert values["ENV"] == "dev"

    def test_chained_transforms(self):
        chain = _make_chain({"MODE": "  production  "})
        result = apply_transforms(chain, [strip_whitespace, to_uppercase])
        values = {v.key: v.resolve() for v in result._vars}
        assert values["MODE"] == "PRODUCTION"

    def test_preserves_profile(self):
        chain = _make_chain({"X": "val"}, profile="staging")
        result = apply_transforms(chain, [to_uppercase])
        assert result.profile == "staging"


class TestTransformKey:
    def test_transforms_single_key(self):
        chain = _make_chain({"SECRET": "abc123"})
        result = transform_key(chain, "SECRET", [to_uppercase])
        assert result == "ABC123"

    def test_raises_for_missing_key(self):
        chain = _make_chain({"A": "val"})
        with pytest.raises(KeyError, match="KEY_X"):
            transform_key(chain, "KEY_X", [to_uppercase])
