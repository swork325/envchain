"""Tests for envchain.cli_scope."""

import io
import json
import os
import tempfile

import pytest

from envchain.cli_scope import build_parser, run_scope


def _write_env(tmp_path, content: str) -> str:
    p = tmp_path / ".env"
    p.write_text(content)
    return str(p)


class TestBuildParser:
    def test_env_file_required(self):
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args([])

    def test_scope_required(self):
        p = build_parser()
        with pytest.raises(SystemExit):
            p.parse_args(["file.env"])

    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["file.env", "DB"])
        assert args.profile == "dev"
        assert args.separator == "_"
        assert args.strip_prefix is False
        assert args.fmt == "dotenv"
        assert args.summary is False

    def test_custom_options(self):
        p = build_parser()
        args = p.parse_args(
            ["file.env", "APP", "--profile", "prod", "--strip-prefix", "--format", "json"]
        )
        assert args.profile == "prod"
        assert args.strip_prefix is True
        assert args.fmt == "json"


class TestRunScope:
    def test_matching_vars_exported(self, tmp_path):
        env_file = _write_env(tmp_path, "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=x\n")
        args = build_parser().parse_args([env_file, "DB"])
        out = io.StringIO()
        rc = run_scope(args, out=out)
        assert rc == 0
        output = out.getvalue()
        assert "DB_HOST" in output
        assert "DB_PORT" in output
        assert "APP_NAME" not in output

    def test_strip_prefix_removes_prefix(self, tmp_path):
        env_file = _write_env(tmp_path, "DB_HOST=localhost\nDB_PORT=5432\n")
        args = build_parser().parse_args([env_file, "DB", "--strip-prefix"])
        out = io.StringIO()
        run_scope(args, out=out)
        output = out.getvalue()
        assert "HOST" in output
        assert "DB_HOST" not in output

    def test_summary_output_is_json(self, tmp_path):
        env_file = _write_env(tmp_path, "DB_HOST=localhost\nAPP_NAME=x\n")
        args = build_parser().parse_args([env_file, "DB", "--summary"])
        out = io.StringIO()
        rc = run_scope(args, out=out)
        assert rc == 0
        data = json.loads(out.getvalue())
        assert data["scope"] == "DB"
        assert data["included"] == 1
        assert data["excluded"] == 1

    def test_empty_scope_prints_comment(self, tmp_path):
        env_file = _write_env(tmp_path, "APP_NAME=x\n")
        args = build_parser().parse_args([env_file, "DB"])
        out = io.StringIO()
        rc = run_scope(args, out=out)
        assert rc == 0
        assert "No variables matched" in out.getvalue()

    def test_json_format(self, tmp_path):
        env_file = _write_env(tmp_path, "DB_HOST=localhost\n")
        args = build_parser().parse_args([env_file, "DB", "--format", "json"])
        out = io.StringIO()
        run_scope(args, out=out)
        data = json.loads(out.getvalue())
        assert "DB_HOST" in data
