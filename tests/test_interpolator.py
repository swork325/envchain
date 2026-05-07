"""Tests for envchain.interpolator."""

from __future__ import annotations

import pytest

from envchain.chain import EnvChain
from envchain.interpolator import InterpolationError, interpolate_chain


def _make_chain(**kwargs: str | None) -> EnvChain:
    chain = EnvChain(profile="test")
    for key, value in kwargs.items():
        chain.add(key, value)
    return chain


class TestInterpolateChain:
    def test_plain_values_unchanged(self):
        chain = _make_chain(HOST="localhost", PORT="5432")
        result = interpolate_chain(chain)
        assert result.get("HOST") == "localhost"
        assert result.get("PORT") == "5432"

    def test_single_reference_resolved(self):
        chain = _make_chain(BASE="http://example.com", URL="${BASE}/api")
        result = interpolate_chain(chain)
        assert result.get("URL") == "http://example.com/api"

    def test_multiple_references_in_one_value(self):
        chain = _make_chain(PROTO="https", HOST="example.com", URL="${PROTO}://${HOST}")
        result = interpolate_chain(chain)
        assert result.get("URL") == "https://example.com"

    def test_nested_reference_resolved(self):
        chain = _make_chain(A="hello", B="${A} world", C="say: ${B}")
        result = interpolate_chain(chain)
        assert result.get("C") == "say: hello world"

    def test_strict_raises_for_missing_ref(self):
        chain = _make_chain(URL="${UNDEFINED}/path")
        with pytest.raises(InterpolationError) as exc_info:
            interpolate_chain(chain, strict=True)
        assert exc_info.value.ref == "UNDEFINED"
        assert exc_info.value.key == "URL"

    def test_non_strict_leaves_unresolved_token(self):
        chain = _make_chain(URL="${GHOST}/path")
        result = interpolate_chain(chain, strict=False)
        assert result.get("URL") == "${GHOST}/path"

    def test_none_value_skipped(self):
        chain = _make_chain(EMPTY=None, HOST="localhost")
        result = interpolate_chain(chain)
        assert result.get("EMPTY") is None

    def test_original_chain_not_mutated(self):
        chain = _make_chain(BASE="http://x.com", URL="${BASE}/v1")
        interpolate_chain(chain)
        assert chain.get("URL") == "${BASE}/v1"

    def test_profile_preserved(self):
        chain = _make_chain(KEY="val")
        result = interpolate_chain(chain)
        assert result.profile == chain.profile


class TestInterpolationError:
    def test_message_contains_key_and_ref(self):
        err = InterpolationError("MY_URL", "MISSING")
        assert "MY_URL" in str(err)
        assert "MISSING" in str(err)

    def test_attributes_set(self):
        err = InterpolationError("K", "R")
        assert err.key == "K"
        assert err.ref == "R"
