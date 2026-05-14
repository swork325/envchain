"""Tests for envchain.cli_tag."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from envchain.cli_tag import build_parser, run_tag


def _write_env(tmp_path: Path, content: str) -> str:
    env_file = tmp_path / ".env"
    env_file.write_text(content)
    return str(env_file)


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_tag_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "tag", "API_KEY", "secret"])
        assert args.command == "tag"
        assert args.key == "API_KEY"
        assert args.tags == ["secret"]

    def test_filter_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "filter", "secret"])
        assert args.command == "filter"
        assert args.tag == "secret"
        assert args.fmt == "text"

    def test_filter_json_format(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "filter", "prod", "--format", "json"])
        assert args.fmt == "json"

    def test_list_tags_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(["myfile.env", "list-tags"])
        assert args.command == "list-tags"


class TestRunTag:
    def test_tag_command_prints_confirmation(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "API_KEY=abc123\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "tag", "API_KEY", "secret", "required"])
        run_tag(args)
        out = capsys.readouterr().out
        assert "API_KEY" in out
        assert "secret" in out

    def test_tag_unknown_key_exits(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "KNOWN=1\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "tag", "UNKNOWN", "x"])
        with pytest.raises(SystemExit) as exc_info:
            run_tag(args)
        assert exc_info.value.code == 1

    def test_filter_text_output(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "DB_URL=postgres://localhost\nLOG=debug\n")
        parser = build_parser()
        # tag first, then filter — use two separate run_tag calls
        args_tag = parser.parse_args([env_file, "tag", "DB_URL", "database"])
        run_tag(args_tag)
        # filter runs on a fresh tagger (no persistence), so filter with no tags
        args_filter = parser.parse_args([env_file, "filter", "database"])
        run_tag(args_filter)
        out = capsys.readouterr().out
        # No tags were persisted — expect the "no variables" message
        assert "No variables tagged" in out

    def test_list_tags_no_tags(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "FOO=bar\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "list-tags"])
        run_tag(args)
        out = capsys.readouterr().out
        assert "No tags" in out
