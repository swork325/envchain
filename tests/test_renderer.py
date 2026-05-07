"""Tests for envchain.renderer."""

from __future__ import annotations

import pytest

from envchain.chain import EnvChain
from envchain.renderer import SUPPORTED_FORMATS, render_chain


def _make_chain(**resolved: str | None) -> EnvChain:
    """Build a chain where each key resolves to the given value (or None)."""
    chain = EnvChain(profile="test")
    for name, value in resolved.items():
        chain.add(name, default=value, required=False)
    return chain


class TestSupportedFormats:
    def test_contains_expected_formats(self):
        assert "table" in SUPPORTED_FORMATS
        assert "summary" in SUPPORTED_FORMATS
        assert "csv" in SUPPORTED_FORMATS

    def test_raises_for_unknown_format(self):
        chain = _make_chain(FOO="bar")
        with pytest.raises(ValueError, match="Unsupported render format"):
            render_chain(chain, fmt="xml")  # type: ignore[arg-type]


class TestTableFormat:
    def test_contains_header(self):
        chain = _make_chain(API_KEY="secret")
        output = render_chain(chain, fmt="table")
        assert "Key" in output
        assert "Value" in output
        assert "Required" in output

    def test_contains_key_and_value(self):
        chain = _make_chain(API_KEY="abc123")
        output = render_chain(chain, fmt="table")
        assert "API_KEY" in output
        assert "abc123" in output

    def test_redact_masks_values(self):
        chain = _make_chain(SECRET="topsecret")
        output = render_chain(chain, fmt="table", redact=True)
        assert "topsecret" not in output
        assert "***" in output

    def test_missing_value_shown(self):
        chain = _make_chain(MISSING=None)
        output = render_chain(chain, fmt="table")
        assert "<missing>" in output

    def test_empty_chain_returns_placeholder(self):
        chain = EnvChain(profile="test")
        output = render_chain(chain, fmt="table")
        assert "empty" in output


class TestCsvFormat:
    def test_has_header_row(self):
        chain = _make_chain(FOO="bar")
        output = render_chain(chain, fmt="csv")
        assert output.startswith("key,value,required")

    def test_contains_key_and_value(self):
        chain = _make_chain(DB_URL="postgres://localhost")
        output = render_chain(chain, fmt="csv")
        assert "DB_URL" in output
        assert "postgres://localhost" in output

    def test_redact_in_csv(self):
        chain = _make_chain(TOKEN="xyz")
        output = render_chain(chain, fmt="csv", redact=True)
        assert "xyz" not in output
        assert "***" in output


class TestSummaryFormat:
    def test_shows_totals(self):
        chain = _make_chain(A="1", B="2", C=None)
        output = render_chain(chain, fmt="summary")
        assert "Total variables" in output
        assert "3" in output

    def test_shows_missing_count(self):
        chain = _make_chain(A="1", B=None)
        output = render_chain(chain, fmt="summary")
        assert "Missing         : 1" in output

    def test_lists_missing_keys(self):
        chain = _make_chain(GONE=None, ALSO_GONE=None)
        output = render_chain(chain, fmt="summary")
        assert "GONE" in output
        assert "ALSO_GONE" in output

    def test_no_missing_line_when_all_present(self):
        chain = _make_chain(X="1", Y="2")
        output = render_chain(chain, fmt="summary")
        assert "Missing keys" not in output
