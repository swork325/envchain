"""Tests for envchain.cli_archive."""

import gzip
import json
import os
import tempfile

import pytest

from envchain.archiver import Archive
from envchain.cli_archive import build_parser, run_capture, run_list, run_restore


def _write_env(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


class TestBuildParser:
    def test_capture_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["capture", "my.env", "archive.gz"])
        assert args.subcommand == "capture"
        assert args.env_file == "my.env"
        assert args.archive_file == "archive.gz"
        assert args.profile == "default"

    def test_list_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["list", "archive.gz", "--profile", "prod"])
        assert args.subcommand == "list"
        assert args.profile == "prod"

    def test_restore_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["restore", "archive.gz", "--format", "json"])
        assert args.subcommand == "restore"
        assert args.format == "json"

    def test_missing_subcommand_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestRunCapture:
    def test_creates_archive_file(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "FOO=bar\nBAZ=qux\n")
            parser = build_parser()
            args = parser.parse_args(["capture", env_path, arc_path, "--profile", "dev"])
            run_capture(args)
            assert os.path.exists(arc_path)
            out = capsys.readouterr().out
            assert "dev" in out

    def test_appends_to_existing_archive(self):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "X=1\n")
            parser = build_parser()
            args = parser.parse_args(["capture", env_path, arc_path])
            run_capture(args)
            run_capture(args)
            loaded = Archive.load(arc_path)
            assert len(loaded.entries) == 2


class TestRunList:
    def test_lists_entries(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "A=1\n")
            parser = build_parser()
            cap_args = parser.parse_args(["capture", env_path, arc_path, "--profile", "staging"])
            run_capture(cap_args)
            list_args = parser.parse_args(["list", arc_path])
            run_list(list_args)
            out = capsys.readouterr().out
            assert "staging" in out

    def test_no_entries_message(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "A=1\n")
            parser = build_parser()
            cap_args = parser.parse_args(["capture", env_path, arc_path, "--profile", "dev"])
            run_capture(cap_args)
            list_args = parser.parse_args(["list", arc_path, "--profile", "prod"])
            run_list(list_args)
            out = capsys.readouterr().out
            assert "No entries" in out


class TestRunRestore:
    def test_restore_dotenv_format(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "MYKEY=hello\n")
            parser = build_parser()
            run_capture(parser.parse_args(["capture", env_path, arc_path]))
            run_restore(parser.parse_args(["restore", arc_path]))
            out = capsys.readouterr().out
            assert "MYKEY=hello" in out

    def test_restore_json_format(self, capsys):
        with tempfile.TemporaryDirectory() as d:
            env_path = os.path.join(d, "test.env")
            arc_path = os.path.join(d, "out.gz")
            _write_env(env_path, "Z=99\n")
            parser = build_parser()
            run_capture(parser.parse_args(["capture", env_path, arc_path]))
            run_restore(parser.parse_args(["restore", arc_path, "--format", "json"]))
            out = capsys.readouterr().out
            data = json.loads(out)
            assert data.get("Z") == "99"
