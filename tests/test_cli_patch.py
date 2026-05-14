"""Tests for envchain.cli_patch."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from envchain.cli_patch import build_parser, run_patch


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
        args = parser.parse_args(["my.env"])
        assert args.profile == "dev"
        assert args.fmt == "dotenv"
        assert args.sets == []
        assert args.removals == []
        assert args.summary is False

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args(
            ["my.env", "--profile", "prod", "--set", "FOO=bar", "--remove", "BAZ", "--format", "json"]
        )
        assert args.profile == "prod"
        assert args.sets == ["FOO=bar"]
        assert args.removals == ["BAZ"]
        assert args.fmt == "json"


class TestRunPatch:
    def test_override_key_appears_in_output(self, tmp_path):
        env_file = _write_env(tmp_path, "FOO=old\nBAR=keep\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--set", "FOO=new", "--format", "dotenv"])
        assert run_patch(args) == 0

    def test_remove_key_absent_from_output(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "FOO=bar\nBAZ=qux\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--remove", "FOO", "--format", "dotenv"])
        run_patch(args)
        captured = capsys.readouterr()
        assert "FOO" not in captured.out
        assert "BAZ" in captured.out

    def test_add_new_key(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "FOO=bar\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--set", "EXTRA=hello", "--format", "dotenv"])
        run_patch(args)
        captured = capsys.readouterr()
        assert "EXTRA" in captured.out

    def test_summary_written_to_stderr(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "FOO=bar\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--set", "FOO=new", "--summary"])
        run_patch(args)
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert "FOO" in data["updated"]

    def test_invalid_set_format_returns_2(self, tmp_path):
        env_file = _write_env(tmp_path, "FOO=bar\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--set", "BADFORMAT"])
        assert run_patch(args) == 2
