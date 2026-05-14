"""Tests for envchain.cli_freeze."""

import json
from pathlib import Path

import pytest

from envchain.cli_freeze import build_parser, run_freeze, run_thaw, run_diff
from envchain.freezer import FrozenChain


def _write_env(tmp_path: Path, content: str) -> str:
    p = tmp_path / ".env"
    p.write_text(content)
    return str(p)


class TestBuildParser:
    def test_freeze_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["freeze", ".env", "out.json"])
        assert args.subcommand == "freeze"
        assert args.env_file == ".env"
        assert args.output == "out.json"
        assert args.profile == "default"

    def test_thaw_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["thaw", "frozen.json"])
        assert args.subcommand == "thaw"
        assert args.fmt == "dotenv"

    def test_diff_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "before.json", "after.json"])
        assert args.subcommand == "diff"
        assert args.before == "before.json"
        assert args.after == "after.json"

    def test_missing_subcommand_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])
            from envchain.cli_freeze import main
            main([])


class TestRunFreeze:
    def test_creates_json_file(self, tmp_path):
        env_file = _write_env(tmp_path, "HOST=localhost\nPORT=5432\n")
        output = str(tmp_path / "frozen.json")
        parser = build_parser()
        args = parser.parse_args(["freeze", env_file, output])
        run_freeze(args)
        data = json.loads(Path(output).read_text())
        assert data["profile"] == "default"
        assert "HOST" in data["values"]
        assert "PORT" in data["values"]

    def test_custom_profile_stored(self, tmp_path):
        env_file = _write_env(tmp_path, "DB=postgres\n")
        output = str(tmp_path / "frozen.json")
        parser = build_parser()
        args = parser.parse_args(["freeze", env_file, output, "--profile", "prod"])
        run_freeze(args)
        data = json.loads(Path(output).read_text())
        assert data["profile"] == "prod"


class TestRunThaw:
    def test_outputs_dotenv(self, tmp_path, capsys):
        fc = FrozenChain(profile="dev", values={"FOO": "bar"})
        frozen_file = tmp_path / "frozen.json"
        frozen_file.write_text(fc.to_json())
        parser = build_parser()
        args = parser.parse_args(["thaw", str(frozen_file)])
        run_thaw(args)
        captured = capsys.readouterr()
        assert "FOO" in captured.out


class TestRunDiff:
    def test_no_diff_message(self, tmp_path, capsys):
        fc = FrozenChain(profile="dev", values={"A": "1"})
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f1.write_text(fc.to_json())
        f2.write_text(fc.to_json())
        parser = build_parser()
        args = parser.parse_args(["diff", str(f1), str(f2)])
        run_diff(args)
        assert "No differences" in capsys.readouterr().out

    def test_diff_shows_changed_key(self, tmp_path, capsys):
        before = FrozenChain(profile="dev", values={"A": "old"})
        after = FrozenChain(profile="dev", values={"A": "new"})
        f1 = tmp_path / "before.json"
        f2 = tmp_path / "after.json"
        f1.write_text(before.to_json())
        f2.write_text(after.to_json())
        parser = build_parser()
        args = parser.parse_args(["diff", str(f1), str(f2)])
        run_diff(args)
        assert "A" in capsys.readouterr().out
