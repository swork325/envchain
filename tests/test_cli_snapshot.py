"""Tests for envchain.cli_snapshot."""

from __future__ import annotations

import json

import pytest

from envchain.cli_snapshot import build_parser, main, run_capture, run_restore


def _write_env(tmp_path, contents: str) -> str:
    p = tmp_path / ".env"
    p.write_text(contents)
    return str(p)


class TestBuildParser:
    def test_capture_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["capture", "file.env", "out.json"])
        assert args.command == "capture"
        assert args.env_file == "file.env"
        assert args.output == "out.json"
        assert args.profile == "default"

    def test_restore_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["restore", "snap.json", "--format", "dotenv"])
        assert args.command == "restore"
        assert args.format == "dotenv"

    def test_missing_subcommand_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestRunCapture:
    def test_creates_snapshot_file(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("MY_KEY", "hello")
        env_file = _write_env(tmp_path, "MY_KEY=ignored\n")
        output = str(tmp_path / "snap.json")
        run_capture(env_file, output, "dev")
        assert (tmp_path / "snap.json").exists()
        out = capsys.readouterr().out
        assert "Snapshot saved" in out

    def test_snapshot_contains_profile(self, tmp_path, monkeypatch):
        env_file = _write_env(tmp_path, "P_VAR=x\n")
        output = str(tmp_path / "snap.json")
        run_capture(env_file, output, "staging")
        with open(output) as fh:
            data = json.load(fh)
        assert data["profile"] == "staging"


class TestRunRestore:
    def test_shell_format_output(self, tmp_path, capsys):
        snap_path = str(tmp_path / "snap.json")
        data = {"profile": "p", "captured_at": "ts", "values": {"FOO": "bar"}}
        (tmp_path / "snap.json").write_text(json.dumps(data))
        run_restore(snap_path, "shell")
        out = capsys.readouterr().out
        assert 'export FOO="bar"' in out

    def test_dotenv_format_output(self, tmp_path, capsys):
        snap_path = str(tmp_path / "snap.json")
        data = {"profile": "p", "captured_at": "ts", "values": {"BAR": "baz"}}
        (tmp_path / "snap.json").write_text(json.dumps(data))
        run_restore(snap_path, "dotenv")
        out = capsys.readouterr().out
        assert "BAR=baz" in out

    def test_none_values_skipped(self, tmp_path, capsys):
        snap_path = str(tmp_path / "snap.json")
        data = {"profile": "p", "captured_at": "ts", "values": {"EMPTY": None}}
        (tmp_path / "snap.json").write_text(json.dumps(data))
        run_restore(snap_path, "shell")
        out = capsys.readouterr().out
        assert "EMPTY" not in out
