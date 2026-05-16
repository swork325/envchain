"""Tests for envchain.cli_inspect."""

import json
import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from envchain.cli_inspect import build_parser, run_inspect


def _write_env(tmp_path: Path, content: str) -> str:
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent(content))
    return str(p)


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["some.env"])
        assert args.env_file == "some.env"
        assert args.profile == "dev"
        assert args.fmt == "text"
        assert args.missing_only is False

    def test_custom_profile_and_format(self):
        parser = build_parser()
        args = parser.parse_args(["x.env", "--profile", "prod", "--format", "json"])
        assert args.profile == "prod"
        assert args.fmt == "json"

    def test_missing_only_flag(self):
        parser = build_parser()
        args = parser.parse_args(["x.env", "--missing-only"])
        assert args.missing_only is True


class TestRunInspect:
    def test_text_output_contains_key(self, tmp_path, monkeypatch, capsys):
        env_file = _write_env(tmp_path, "APP_HOST=localhost\n")
        monkeypatch.setenv("APP_HOST", "localhost")
        parser = build_parser()
        args = parser.parse_args([env_file, "--profile", "dev"])
        run_inspect(args)
        out = capsys.readouterr().out
        assert "APP_HOST" in out

    def test_json_output_is_valid(self, tmp_path, monkeypatch, capsys):
        env_file = _write_env(tmp_path, "DB_URL=postgres://localhost\n")
        monkeypatch.setenv("DB_URL", "postgres://localhost")
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json"])
        run_inspect(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "entries" in data
        assert data["profile"] == "dev"

    def test_missing_only_filters_output(self, tmp_path, monkeypatch, capsys):
        env_file = _write_env(tmp_path, "PRESENT=yes\nABSENT=\n")
        monkeypatch.setenv("PRESENT", "yes")
        monkeypatch.delenv("ABSENT", raising=False)
        parser = build_parser()
        args = parser.parse_args([env_file, "--missing-only"])
        run_inspect(args)
        out = capsys.readouterr().out
        assert "ABSENT" in out or "No entries" in out

    def test_json_missing_only_returns_subset(self, tmp_path, monkeypatch, capsys):
        env_file = _write_env(tmp_path, "FOUND=1\nLOST=\n")
        monkeypatch.setenv("FOUND", "1")
        monkeypatch.delenv("LOST", raising=False)
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json", "--missing-only"])
        run_inspect(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        keys = [e["key"] for e in data["entries"]]
        assert "FOUND" not in keys
