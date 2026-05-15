"""Tests for envchain.cli_trace."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from envchain.cli_trace import build_parser, run_trace


def _write_env(tmp_path: Path, filename: str, content: str) -> str:
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


class TestBuildParser:
    def test_env_files_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_single_env_file_accepted(self):
        parser = build_parser()
        args = parser.parse_args(["file.env"])
        assert args.env_files == ["file.env"]

    def test_multiple_env_files_accepted(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert args.env_files == ["a.env", "b.env"]

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["file.env"])
        assert args.profile == "dev"
        assert args.format == "text"
        assert args.key is None

    def test_custom_key_and_format(self):
        parser = build_parser()
        args = parser.parse_args(["file.env", "--key", "DB_URL", "--format", "json"])
        assert args.key == "DB_URL"
        assert args.format == "json"


class TestRunTrace:
    def test_text_output_for_all_keys(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "dev.env", "API_KEY=secret\nDEBUG=true\n")
        parser = build_parser()
        args = parser.parse_args([env_file])
        run_trace(args)
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "DEBUG" in out

    def test_text_output_single_key(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "dev.env", "API_KEY=secret\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--key", "API_KEY"])
        run_trace(args)
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "DEBUG" not in out

    def test_json_output_is_valid(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "dev.env", "FOO=bar\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json"])
        run_trace(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert data[0]["key"] == "FOO"

    def test_json_single_key_output(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "dev.env", "FOO=bar\nBAZ=qux\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--key", "FOO", "--format", "json"])
        run_trace(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["key"] == "FOO"

    def test_multiple_files_produce_multiple_steps(self, tmp_path, capsys):
        f1 = _write_env(tmp_path, "a.env", "X=1\n")
        f2 = _write_env(tmp_path, "b.env", "X=2\n")
        parser = build_parser()
        args = parser.parse_args([f1, f2, "--key", "X", "--format", "json"])
        run_trace(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data[0]["steps"]) == 2
