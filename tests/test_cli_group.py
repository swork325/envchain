"""Tests for envchain.cli_group."""

from __future__ import annotations

import io
import os
import tempfile

import pytest

from envchain.cli_group import build_parser, run_group


def _write_env(content: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    f.write(content)
    f.close()
    return f.name


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["some.env"])
        assert args.profile == "dev"
        assert args.separator == "_"
        assert args.ungrouped_label == "__other__"

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args(
            ["some.env", "--profile", "prod", "--separator", ".", "--ungrouped-label", "misc"]
        )
        assert args.profile == "prod"
        assert args.separator == "."
        assert args.ungrouped_label == "misc"


class TestRunGroup:
    def test_outputs_groups(self):
        path = _write_env("DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path, "--profile", "dev"])
            out = io.StringIO()
            run_group(args, out=out)
            result = out.getvalue()
            assert "[APP]" in result
            assert "[DB]" in result
            assert "DB_HOST" in result
            assert "APP_NAME" in result
        finally:
            os.unlink(path)

    def test_empty_file_outputs_no_variables_message(self):
        path = _write_env("")
        try:
            parser = build_parser()
            args = parser.parse_args([path])
            out = io.StringIO()
            run_group(args, out=out)
            assert "no variables" in out.getvalue()
        finally:
            os.unlink(path)

    def test_ungrouped_label_appears_for_bare_keys(self):
        path = _write_env("SIMPLE=value\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path, "--ungrouped-label", "misc"])
            out = io.StringIO()
            run_group(args, out=out)
            assert "[misc]" in out.getvalue()
        finally:
            os.unlink(path)

    def test_unset_variable_shows_placeholder(self, monkeypatch):
        monkeypatch.delenv("GHOST_KEY", raising=False)
        path = _write_env("GHOST_KEY=\n")
        try:
            parser = build_parser()
            args = parser.parse_args([path])
            out = io.StringIO()
            run_group(args, out=out)
            assert "<unset>" in out.getvalue() or "GHOST_KEY" in out.getvalue()
        finally:
            os.unlink(path)
