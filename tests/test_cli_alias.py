"""Tests for envchain.cli_alias."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from envchain.cli_alias import build_parser, _parse_alias_args, run_alias


def _write_env(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return tmp.name


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
        assert args.aliases == []
        assert args.fmt == "text"

    def test_custom_profile_and_format(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--profile", "staging", "--format", "json"])
        assert args.profile == "staging"
        assert args.fmt == "json"

    def test_alias_flag_accumulates(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--alias", "DB_HOST=host", "--alias", "API_KEY=key"])
        assert args.aliases == ["DB_HOST=host", "API_KEY=key"]


class TestParseAliasArgs:
    def test_parses_single_mapping(self):
        result = _parse_alias_args(["DB_HOST=database_host"])
        assert result == {"DB_HOST": "database_host"}

    def test_parses_multiple_mappings(self):
        result = _parse_alias_args(["A=alpha", "B=beta"])
        assert result == {"A": "alpha", "B": "beta"}

    def test_raises_for_missing_equals(self):
        with pytest.raises(ValueError, match="Invalid alias spec"):
            _parse_alias_args(["NOEQUALS"])

    def test_empty_list_returns_empty_dict(self):
        assert _parse_alias_args([]) == {}


class TestRunAlias:
    def test_text_output_contains_profile(self, capsys):
        path = _write_env("DB_HOST=localhost\nAPI_KEY=secret\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path, "--profile", "dev"])
            run_alias(args)
            out = capsys.readouterr().out
            assert "dev" in out
        finally:
            os.unlink(path)

    def test_text_output_shows_alias_arrow(self, capsys):
        path = _write_env("DB_HOST=localhost\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path, "--alias", "DB_HOST=database_host"])
            run_alias(args)
            out = capsys.readouterr().out
            assert "-> database_host" in out
        finally:
            os.unlink(path)

    def test_json_output_is_valid(self, capsys):
        path = _write_env("DB_HOST=localhost\nAPI_KEY=secret\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path, "--format", "json", "--alias", "DB_HOST=host"])
            run_alias(args)
            out = capsys.readouterr().out
            data = json.loads(out)
            assert "profile" in data
            assert "entries" in data
            keys = [e["key"] for e in data["entries"]]
            assert "DB_HOST" in keys
        finally:
            os.unlink(path)
