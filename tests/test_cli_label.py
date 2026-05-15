"""Tests for envchain.cli_label."""

import json
import os
import textwrap
from pathlib import Path

import pytest

from envchain.cli_label import build_parser, run_label, _parse_label_args


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
        assert args.labels == []
        assert args.filter_label is None

    def test_custom_profile(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--profile", "prod"])
        assert args.profile == "prod"

    def test_label_flag_appends(self):
        parser = build_parser()
        args = parser.parse_args(
            ["my.env", "--label", "DB_URL=tier:database", "--label", "API_KEY=tier:auth"]
        )
        assert len(args.labels) == 2

    def test_filter_label_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--filter-label", "tier:database"])
        assert args.filter_label == "tier:database"


class TestParseLabelArgs:
    def test_single_label(self):
        rules = _parse_label_args(["DB_URL=tier:database"])
        assert rules == {"DB_URL": {"tier": "database"}}

    def test_multiple_labels_same_key(self):
        rules = _parse_label_args(
            ["DB_URL=tier:database", "DB_URL=sensitive:false"]
        )
        assert rules["DB_URL"] == {"tier": "database", "sensitive": "false"}

    def test_multiple_keys(self):
        rules = _parse_label_args(
            ["DB_URL=tier:database", "API_KEY=tier:auth"]
        )
        assert "DB_URL" in rules
        assert "API_KEY" in rules


class TestRunLabel:
    def test_outputs_all_vars_as_json(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, """\
            DB_URL=postgres://localhost
            LOG_LEVEL=debug
        """)
        parser = build_parser()
        args = parser.parse_args([env_file])
        run_label(args)
        out = json.loads(capsys.readouterr().out)
        keys = [e["key"] for e in out]
        assert "DB_URL" in keys
        assert "LOG_LEVEL" in keys

    def test_labels_appear_in_output(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "API_KEY=secret\n")
        parser = build_parser()
        args = parser.parse_args(
            [env_file, "--label", "API_KEY=tier:auth"]
        )
        run_label(args)
        out = json.loads(capsys.readouterr().out)
        entry = next(e for e in out if e["key"] == "API_KEY")
        assert entry["labels"]["tier"] == "auth"

    def test_filter_label_restricts_output(self, tmp_path, capsys):
        env_file = _write_env(tmp_path, "DB_URL=pg\nLOG_LEVEL=info\n")
        parser = build_parser()
        args = parser.parse_args(
            [
                env_file,
                "--label", "DB_URL=tier:database",
                "--filter-label", "tier:database",
            ]
        )
        run_label(args)
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["key"] == "DB_URL"
