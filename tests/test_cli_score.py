"""Tests for envchain.cli_score."""

import io
import json
import os
import tempfile
import pytest

from envchain.cli_score import build_parser, run_score


def _write_env(tmp_path, content: str) -> str:
    p = tmp_path / ".env"
    p.write_text(content)
    return str(p)


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
        assert args.fmt == "text"
        assert args.fail_below is None

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args(["x.env", "--profile", "prod", "--format", "json", "--fail-below", "0.8"])
        assert args.profile == "prod"
        assert args.fmt == "json"
        assert args.fail_below == pytest.approx(0.8)


class TestRunScore:
    def test_text_output_contains_profile(self, tmp_path):
        env_file = _write_env(tmp_path, "DB_URL=postgres\nSECRET=abc\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--profile", "dev"])
        out = io.StringIO()
        run_score(args, out=out)
        assert "dev" in out.getvalue()

    def test_text_output_contains_score_keys(self, tmp_path):
        env_file = _write_env(tmp_path, "A=1\nB=2\n")
        parser = build_parser()
        args = parser.parse_args([env_file])
        out = io.StringIO()
        run_score(args, out=out)
        assert "completeness" in out.getvalue()
        assert "Overall" in out.getvalue()

    def test_json_output_is_valid(self, tmp_path):
        env_file = _write_env(tmp_path, "X=hello\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json"])
        out = io.StringIO()
        run_score(args, out=out)
        data = json.loads(out.getvalue())
        assert "overall" in data
        assert "scores" in data
        assert data["total"] >= 1

    def test_fail_below_returns_1_when_score_low(self, tmp_path):
        env_file = _write_env(tmp_path, "")
        parser = build_parser()
        args = parser.parse_args([env_file, "--fail-below", "0.9"])
        out = io.StringIO()
        code = run_score(args, out=out)
        assert code == 1

    def test_fail_below_returns_0_when_score_sufficient(self, tmp_path):
        env_file = _write_env(tmp_path, "A=1\nB=2\nC=3\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--fail-below", "0.0"])
        out = io.StringIO()
        code = run_score(args, out=out)
        assert code == 0

    def test_no_fail_below_always_returns_0(self, tmp_path):
        env_file = _write_env(tmp_path, "")
        parser = build_parser()
        args = parser.parse_args([env_file])
        out = io.StringIO()
        code = run_score(args, out=out)
        assert code == 0
