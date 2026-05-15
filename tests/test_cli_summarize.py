"""Tests for envchain.cli_summarize."""

import io
import json
import os
import tempfile

import pytest

from envchain.cli_summarize import build_parser, run_summarize


def _write_env(tmp_path, contents: str) -> str:
    p = tmp_path / ".env"
    p.write_text(contents)
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
        assert args.profile == "default"
        assert args.output_format == "text"

    def test_custom_profile_and_format(self):
        parser = build_parser()
        args = parser.parse_args(["my.env", "--profile", "prod", "--format", "json"])
        assert args.profile == "prod"
        assert args.output_format == "json"


class TestRunSummarizeText:
    def test_text_output_contains_profile(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DB_HOST", "localhost")
        env_file = _write_env(tmp_path, "DB_HOST=\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--profile", "staging"])
        out = io.StringIO()
        run_summarize(args, out=out)
        result = out.getvalue()
        assert "staging" in result
        assert "Total" in result

    def test_text_output_shows_missing_keys(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        env_file = _write_env(tmp_path, "SECRET_KEY=\n")
        parser = build_parser()
        args = parser.parse_args([env_file])
        out = io.StringIO()
        run_summarize(args, out=out)
        result = out.getvalue()
        assert "SECRET_KEY" in result

    def test_text_output_no_missing_section_when_all_present(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APP_PORT", "8080")
        env_file = _write_env(tmp_path, "APP_PORT=\n")
        parser = build_parser()
        args = parser.parse_args([env_file])
        out = io.StringIO()
        run_summarize(args, out=out)
        result = out.getvalue()
        assert "Missing keys" not in result


class TestRunSummarizeJson:
    def test_json_output_is_valid(self, tmp_path, monkeypatch):
        monkeypatch.setenv("API_URL", "https://example.com")
        env_file = _write_env(tmp_path, "API_URL=\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json"])
        out = io.StringIO()
        run_summarize(args, out=out)
        data = json.loads(out.getvalue())
        assert "profile" in data
        assert "total" in data
        assert "missing_keys" in data

    def test_json_missing_key_listed(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GONE_VAR", raising=False)
        env_file = _write_env(tmp_path, "GONE_VAR=\n")
        parser = build_parser()
        args = parser.parse_args([env_file, "--format", "json"])
        out = io.StringIO()
        run_summarize(args, out=out)
        data = json.loads(out.getvalue())
        assert "GONE_VAR" in data["missing_keys"]
        assert data["missing"] == 1
