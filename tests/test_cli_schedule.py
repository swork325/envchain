"""Tests for envchain.cli_schedule."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from envchain.cli_schedule import build_parser, _make_audit_callback
from envchain.chain import EnvChain


def _write_env(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(content))
    return p


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["my.env"])
        assert args.env_file == "my.env"
        assert args.profile == "dev"
        assert args.interval == 30.0
        assert args.require == []

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args(
            ["my.env", "--profile", "prod", "--interval", "60", "--require", "DB_URL", "API_KEY"]
        )
        assert args.profile == "prod"
        assert args.interval == 60.0
        assert args.require == ["DB_URL", "API_KEY"]


class TestAuditCallback:
    def _chain_with(self, **kwargs: str) -> EnvChain:
        chain = EnvChain(profile="test")
        for k, v in kwargs.items():
            chain.add(k, v)
        return chain

    def test_passes_when_required_keys_present(self, capsys):
        chain = self._chain_with(DB_URL="postgres://localhost/db")
        cb = _make_audit_callback(["DB_URL"])
        cb(chain)
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_fails_when_required_key_missing(self, capsys):
        chain = self._chain_with()
        cb = _make_audit_callback(["MISSING_KEY"])
        cb(chain)
        out = capsys.readouterr().out
        assert "FAIL" in out
        assert "MISSING_KEY" in out

    def test_no_required_keys_always_passes(self, capsys):
        chain = self._chain_with()
        cb = _make_audit_callback([])
        cb(chain)
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_output_contains_profile(self, capsys):
        chain = EnvChain(profile="staging")
        chain.add("X", "1")
        cb = _make_audit_callback(["X"])
        cb(chain)
        out = capsys.readouterr().out
        assert "staging" in out
