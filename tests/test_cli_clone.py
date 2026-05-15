"""Tests for envchain.cli_clone."""

import io
import json
import os
import tempfile

import pytest

from envchain.cli_clone import build_parser, run_clone


def _write_env(path: str, content: str) -> None:
    with open(path, "w") as fh:
        fh.write(content)


class TestBuildParser:
    def test_env_file_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["my.env"])
        assert args.env_file == "my.env"
        assert args.source_profile == "dev"
        assert args.target_profile == "staging"
        assert args.fmt == "dotenv"
        assert args.uppercase_keys is False
        assert args.summary is False
        assert args.exclude == []

    def test_custom_options(self):
        parser = build_parser()
        args = parser.parse_args([
            "prod.env",
            "--source-profile", "staging",
            "--target-profile", "prod",
            "--format", "json",
            "--uppercase-keys",
            "--summary",
            "--exclude", "SECRET_KEY", "DEBUG",
        ])
        assert args.source_profile == "staging"
        assert args.target_profile == "prod"
        assert args.fmt == "json"
        assert args.uppercase_keys is True
        assert args.summary is True
        assert args.exclude == ["SECRET_KEY", "DEBUG"]


class TestRunClone:
    def _args(self, env_file, **kwargs):
        parser = build_parser()
        base = [env_file]
        for k, v in kwargs.items():
            flag = "--" + k.replace("_", "-")
            if isinstance(v, bool):
                if v:
                    base.append(flag)
            elif isinstance(v, list):
                base += [flag] + v
            else:
                base += [flag, str(v)]
        return parser.parse_args(base)

    def test_clone_produces_dotenv_output(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("DB_HOST=localhost\nDB_PORT=5432\n")
            name = f.name
        try:
            args = self._args(name)
            out = io.StringIO()
            rc = run_clone(args, out=out)
            assert rc == 0
            content = out.getvalue()
            assert "DB_HOST" in content
            assert "DB_PORT" in content
        finally:
            os.unlink(name)

    def test_summary_flag_returns_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("API_KEY=secret\n")
            name = f.name
        try:
            args = self._args(name, summary=True)
            out = io.StringIO()
            rc = run_clone(args, out=out)
            assert rc == 0
            data = json.loads(out.getvalue())
            assert "cloned" in data
            assert "skipped" in data
            assert data["source_profile"] == "dev"
            assert data["target_profile"] == "staging"
        finally:
            os.unlink(name)

    def test_exclude_removes_key_from_clone(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("KEEP=yes\nDROP=no\n")
            name = f.name
        try:
            args = self._args(name, summary=True, exclude=["DROP"])
            out = io.StringIO()
            rc = run_clone(args, out=out)
            assert rc == 0
            data = json.loads(out.getvalue())
            assert "DROP" in data["skipped"]
            assert "KEEP" in data["cloned"]
        finally:
            os.unlink(name)

    def test_invalid_target_profile_returns_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("X=1\n")
            name = f.name
        try:
            parser = build_parser()
            with pytest.raises(SystemExit):
                parser.parse_args([name, "--target-profile", "nope"])
        finally:
            os.unlink(name)
